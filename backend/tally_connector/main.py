import logging
from contextlib import asynccontextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from decouple import config as env_config
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .api.tally_client import CloudAPIClient, TallyClient
from .database.local_cache import LocalCache
from .scheduler.sync_scheduler import SyncScheduler
from .security.auth import verify_backend_request


def setup_logging(log_dir: str) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "connector.log"

    formatter = logging.Formatter(
        "[TallyConnector] %(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


class ConnectorConfig(BaseModel):
    backend_base_url: str = Field(default_factory=lambda: env_config("CONNECTOR_BACKEND_URL", default="http://127.0.0.1:8000"))
    backend_api_token: str = Field(default_factory=lambda: env_config("CONNECTOR_API_TOKEN", default=""))
    company_id: str = Field(default_factory=lambda: env_config("CONNECTOR_COMPANY_ID", default=""))
    company_name: str = Field(default_factory=lambda: env_config("CONNECTOR_TALLY_COMPANY", default=""))
    tally_host: str = Field(default_factory=lambda: env_config("CONNECTOR_TALLY_HOST", default="127.0.0.1"))
    tally_port: int = Field(default_factory=lambda: env_config("CONNECTOR_TALLY_PORT", default=9000, cast=int))
    db_path: str = Field(default_factory=lambda: env_config("CONNECTOR_DB_PATH", default="./connector_cache.sqlite3"))
    log_dir: str = Field(default_factory=lambda: env_config("CONNECTOR_LOG_DIR", default="./logs"))

    ledger_sync_interval: int = Field(default_factory=lambda: env_config("CONNECTOR_LEDGER_SYNC_SEC", default=60, cast=int))
    voucher_sync_interval: int = Field(default_factory=lambda: env_config("CONNECTOR_VOUCHER_SYNC_SEC", default=30, cast=int))
    stock_sync_interval: int = Field(default_factory=lambda: env_config("CONNECTOR_STOCK_SYNC_SEC", default=300, cast=int))
    task_worker_interval: int = Field(default_factory=lambda: env_config("CONNECTOR_TASK_WORKER_SEC", default=10, cast=int))


class ConnectorService:
    def __init__(self, config: ConnectorConfig):
        self.config = config.model_dump()
        setup_logging(config.log_dir)
        self.logger = logging.getLogger("tally_connector")

        self.cache = LocalCache(config.db_path)
        self.device_id = self.cache.get_or_create_device_id()

        self.tally_client = TallyClient(
            host=config.tally_host,
            port=config.tally_port,
            timeout_seconds=20,
            max_retries=3,
        )
        self.cloud_client = CloudAPIClient(
            base_url=config.backend_base_url,
            api_token=config.backend_api_token,
            company_id=config.company_id,
            device_id=self.device_id,
            timeout_seconds=20,
            max_retries=3,
        )
        self.company_name = config.company_name
        self.scheduler = SyncScheduler(self)

    async def startup(self) -> None:
        running = await self.tally_client.is_tally_running()
        if not running:
            detected = await self.tally_client.detect_port()
            if detected is None:
                self.logger.warning("Tally is not reachable during startup. Connector will retry in jobs.")
            else:
                self.logger.info("Detected Tally XML server on port %s", detected)

        await self.scheduler.start()
        self.logger.info("Connector service started")

    async def shutdown(self) -> None:
        await self.scheduler.stop()
        self.logger.info("Connector service stopped")


config = ConnectorConfig()
service = ConnectorService(config)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await service.startup()
    try:
        yield
    finally:
        await service.shutdown()


app = FastAPI(
    title="SIZH Local Tally Connector",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ManualSyncRequest(BaseModel):
    entities: list[str] = Field(default_factory=lambda: ["ledgers", "vouchers", "stock_items"])
    sync_type: str = "manual"


class PushCommandRequest(BaseModel):
    operation: str
    data: dict[str, Any]
    dedupe_key: str | None = None
    callback_endpoint: str | None = None
    callback_reference_id: str | None = None


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "local_tally_connector",
        "timestamp": datetime.utcnow().isoformat(),
        "device_id": service.device_id,
        "tally_host": service.tally_client.host,
        "tally_port": service.tally_client.port,
        "pending_tasks": service.cache.pending_summary(),
    }


@app.get("/tally/status")
async def tally_status() -> dict[str, Any]:
    running = await service.tally_client.is_tally_running()
    return {
        "running": running,
        "host": service.tally_client.host,
        "port": service.tally_client.port,
        "company_name": service.company_name,
    }


@app.post("/sync/manual", dependencies=[Depends(verify_backend_request)])
async def manual_sync(payload: ManualSyncRequest) -> dict[str, Any]:
    results = await service.scheduler.run_manual_sync(payload.entities, payload.sync_type)
    return {"status": "completed", "results": results}


@app.post("/commands/push", dependencies=[Depends(verify_backend_request)])
async def queue_push_command(payload: PushCommandRequest) -> dict[str, Any]:
    callback = {}
    if payload.callback_endpoint:
        callback = {
            "endpoint": payload.callback_endpoint,
            "reference_id": payload.callback_reference_id or "",
        }

    accepted, task_id = service.cache.enqueue_task(
        task_type="push_to_tally",
        entity=payload.operation,
        dedupe_key=payload.dedupe_key,
        payload={
            "operation": payload.operation,
            "data": payload.data,
            "callback": callback,
        },
    )

    if not accepted:
        raise HTTPException(status_code=409, detail="Duplicate command ignored")

    return {"status": "queued", "task_id": task_id}


@app.post("/commands/process", dependencies=[Depends(verify_backend_request)])
async def process_commands() -> dict[str, Any]:
    await service.scheduler.process_pending_tasks()
    return {"status": "processed", "pending": service.cache.pending_summary()}


@app.get("/tasks/summary", dependencies=[Depends(verify_backend_request)])
async def task_summary() -> dict[str, Any]:
    return service.cache.pending_summary()
