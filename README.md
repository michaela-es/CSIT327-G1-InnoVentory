# 🧾 InnoVentory

> A smart, web-based inventory and business management system built for small and medium enterprises (SMEs).
> 

[Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)

[Django](https://img.shields.io/badge/Django-5.x-green?logo=django)

[PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-blue?logo=postgresql)

[Render](https://img.shields.io/badge/Deployed-Render-46b3e3?logo=render)

---

## 📘 Overview

**InnoVentory** is a web-based system designed to simplify inventory tracking, sales monitoring, and business record-keeping for small and medium enterprises.

It integrates an intuitive user interface with a robust backend to:

- ✅ Streamline daily operations
- 🧠 Reduce human error
- 📊 Provide real-time data insights
- 👥 Manage users and roles efficiently

---

## 🧩 Tech Stack

| Layer | Technology |
| --- | --- |
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | Python (Django Framework) |
| **Database** | PostgreSQL (Supabase) |
| **Deployment** | [Render.com](http://render.com/) |
| **Static Files** | WhiteNoise |
| **WSGI Server** | Gunicorn |

---

## 🚀 Quick Deployment (Render + Supabase)

### Prerequisites

- GitHub repository with Django app
- Supabase project (PostgreSQL)
- [Render.com](http://render.com/) account

### 1. Environment Setup

**requirements.txt:**

```
Django>=4.2,<5.1
gunicorn>=21.2
whitenoise>=6.6
dj-database-url>=2.2
psycopg[binary]>=3.2
python-dotenv>=1.0

```

**.env.example:**

```
# Django
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-render-service.onrender.com,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-render-service.onrender.com

# Database (Supabase)
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require

# Security
DJANGO_SECURE_SSL_REDIRECT=True

```

### 2. Django Configuration

[**settings.py](http://settings.py/):**

```python
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env in local dev only
if os.environ.get("RENDER", "") != "true":
    load_dotenv()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}

# Static Files (WhiteNoise)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ... other middleware
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Security
if os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

```

### 3. Build Script

[**build.sh](http://build.sh/):**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running database migrations"
python manage.py makemigrations
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build complete"

```

Make executable: `chmod +x build.sh`

### 4. Render Deployment

1. **Create Web Service** on [Render.com](http://render.com/)
2. **Connect GitHub repository**
3. **Build Settings:**
    - Build Command: `./build.sh`
    - Start Command: `gunicorn your_project.wsgi:application`
4. **Environment Variables:**
    
    ```
    RENDER=true
    DJANGO_SECRET_KEY=your-generated-secret-key
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=your-service.onrender.com
    DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service.onrender.com
    DATABASE_URL=your-supabase-connection-string
    
    ```
    

### 5. Supabase Connection

**Use Connection Pooler (Recommended):**

- Go to Supabase project → Settings → Database
- Use **Pooler connection string**:
    
    ```
    postgresql://postgres.[project-ref]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
    
    ```
    

**Direct Connection:**

```
postgresql://postgres.[project-ref]:[password]@db.[project-ref].supabase.co:5432/postgres?sslmode=require

```

**Key Points:**

- Always include `?sslmode=require`
- Pooler uses port `6543`, direct uses `5432`
- Pooler handles many short connections better

---

## 🛠 Local Development

### 1️⃣ Clone the Repository

```bash
git clone <https://github.com/><your-repo>/innoventory.git
cd innoventory

```

### 2️⃣ Create and Activate Virtual Environment

```bash
python -m venv venv
venv\\Scripts\\activate        # Windows
source venv/bin/activate     # macOS/Linux

```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt

```

### 4️⃣ Configure Environment

```bash
cp .env.example .env
# Edit .env with your local values

```

### 5️⃣ Run Migrations

```bash
python manage.py migrate

```

### 6️⃣ Create Superuser

```bash
python manage.py createsuperuser

```

### 7️⃣ Run Development Server

```bash
python manage.py runserver

```

Visit: [http://127.0.0.1:8000](http://127.0.0.1:8000/)
</details>

---

## 👥 Team Members

**Michelle Marie P. Habon** — Business Analyst — [michellemarie.habon@cit.edu](mailto:michellemarie.habon@cit.edu)

**Tovi Joshua J. Hermosisima** — Scrum Master — [tovijoshua.hermosisima@cit.edu](mailto:tovijoshua.hermosisima@cit.edu)

**Ashley N. Igonia** — Product Owner — [ashley.igonia@cit.edu](mailto:ashley.igonia@cit.edu)

**Kenn Xavier C. Dabon** — Developer — [kenn.dabon@cit.edu](mailto:kenn.dabon@cit.edu)

**Shinely Marie R. Embalsado** — Developer — [shinelymarie.embalsado@cit.edu](mailto:shinelymarie.embalsado@cit.edu)

**Michaela Ma. Alexa D. Estrera** — Lead Developer — [michaelamaalexa.estrera@cit.edu](mailto:michaelamaalexa.estrera@cit.edu)

---

Deployed Link: https://innoventory.onrender.com
