# CoProduct Backend (M1)

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

or if run service on dev-env:

```bash
cd backend
source ../.venv/bin/activate
pip install -e .

cp .env.example .env

export COPRODUCT_DATABASE_URL="sqlite+pysqlite:///./coproduct.db"
export COPRODUCT_UPLOAD_DIR="./uploaded_files"
export COPRODUCT_AUTH_MODE="jwt"
export COPRODUCT_BOOTSTRAP_OWNER_API_KEY="cpk_dev_local_bootstrap_key_change_me"

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```


## Auth

Use header:

```text
Authorization: Bearer dev-token
```

