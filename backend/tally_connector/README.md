# Local Tally Connector

This package implements a local connector bridge between cloud backend APIs and local Tally XML API.

## Architecture

Web App UI -> Cloud Backend API -> Local Connector -> Tally XML API -> Tally Engine

The connector keeps a local SQLite cache for:
- Last sync timestamps
- Sync logs
- Pending push commands
- Fingerprints for dedupe and incremental sync behavior

## Modules

- api/tally_client.py
  - Tally HTTP XML communication with retry and port detection
  - Cloud API client with token + company + device headers
- api/xml_builder.py
  - Export request builders
  - Import payload builders for ledger, voucher, stock item
- parser/xml_parser.py
  - XML to normalized dicts for ledgers, vouchers, stock items
- sync/ledger_sync.py
- sync/voucher_sync.py
- sync/stock_sync.py
  - Pull from Tally, parse, dedupe, push changed records to cloud
- scheduler/sync_scheduler.py
  - Scheduled sync loops and pending command worker
- security/auth.py
  - Backend token and company validation for local API endpoints
- database/local_cache.py
  - SQLite local cache and retry queue
- main.py
  - FastAPI app startup and public connector endpoints

## Supported Push Operations

- create_ledger
- create_customer (as ledger under Sundry Debtors)
- create_supplier (as ledger under Sundry Creditors)
- create_voucher
- create_stock_item

## Environment Variables

- CONNECTOR_BACKEND_URL
- CONNECTOR_API_TOKEN
- CONNECTOR_COMPANY_ID
- CONNECTOR_TALLY_COMPANY
- CONNECTOR_TALLY_HOST
- CONNECTOR_TALLY_PORT
- CONNECTOR_DB_PATH
- CONNECTOR_LOG_DIR
- CONNECTOR_LEDGER_SYNC_SEC
- CONNECTOR_VOUCHER_SYNC_SEC
- CONNECTOR_STOCK_SYNC_SEC
- CONNECTOR_TASK_WORKER_SEC

## Run

From backend folder:

uvicorn tally_connector.main:app --host 127.0.0.1 --port 8765

## Security Notes

- Use HTTPS on CONNECTOR_BACKEND_URL.
- Keep CONNECTOR_API_TOKEN unique per tenant/company.
- Validate X-Company-ID on every command call.
- Register connector device_id with backend for trust and traceability.
