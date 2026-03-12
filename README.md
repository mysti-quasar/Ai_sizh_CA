# SIZH CA - AI-Powered Accounting & Tally Automation Suite

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), Tailwind CSS, Zustand, Lucide Icons |
| Core Backend | Django 6 + Django REST Framework, SimpleJWT |
| Database | PostgreSQL |
| Cache/Queue | Valkey (Redis-compatible) |
| Microservice | FastAPI (Phase 2) |

## Project Structure

```
Sizh_CA_structure/
├── backend/                    # Django Backend
│   ├── config/                 # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── accounts/               # Custom User, Auth, JWT
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── clients/                # Client Profile (Multi-tenancy)
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── signals.py
│   ├── documents/              # Document Vault
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── manage.py
│   └── .env
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── (dashboard)/    # All authenticated routes
│   │   │   │   ├── dashboard/
│   │   │   │   ├── bulk-upload/
│   │   │   │   ├── master/
│   │   │   │   ├── transaction/
│   │   │   │   ├── gst-reco/
│   │   │   │   ├── document/
│   │   │   │   ├── analysis/
│   │   │   │   ├── reports/
│   │   │   │   ├── ca-gpt/
│   │   │   │   ├── settings/
│   │   │   │   └── layout.tsx
│   │   │   ├── login/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── layout/         # Sidebar, Topbar, AppLayout
│   │   │   └── documents/      # FolderTree, FileList
│   │   ├── store/              # Zustand stores
│   │   │   ├── auth-store.ts
│   │   │   └── client-store.ts
│   │   └── lib/                # API client, utilities
│   │       ├── api.ts
│   │       └── utils.ts
│   └── .env.local
├── venv/                       # Python virtual environment
└── requirements.txt
```

## Quick Start

### 1. Backend Setup

```bash
# Activate virtual environment
source venv/bin/activate

# macOS (if createdb is missing)
brew install postgresql@16
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
brew services start postgresql@16

# Configure PostgreSQL (create database)
createdb sizh_ca_db

# Run migrations
cd backend
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login (JWT tokens) |
| POST | `/api/auth/token/refresh/` | Refresh JWT token |
| GET/PATCH | `/api/auth/profile/` | User profile |
| GET/POST | `/api/clients/` | List/Create client profiles |
| GET/PATCH/DELETE | `/api/clients/<id>/` | Client profile detail |
| POST | `/api/clients/switch/` | Switch active client |
| GET | `/api/clients/active/` | Get active client |
| GET | `/api/documents/folders/` | List document folders |
| POST | `/api/documents/folders/create/` | Create folder |
| POST | `/api/documents/init-folders/` | Init default folders |
| GET | `/api/documents/folders/<id>/files/` | List files in folder |
| POST | `/api/documents/folders/<id>/files/upload/` | Upload file |
