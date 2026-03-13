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

uvicorn app.main:app --reload --host localhost --port 8000
```

Cloud model mode (OpenAI-compatible / DeepSeek):

```bash
export COPRODUCT_MODEL_MODE="cloud"
export COPRODUCT_MODEL_PROVIDER="openai_compatible"
export COPRODUCT_MODEL_API_KEY="<your-api-key>"
export COPRODUCT_MODEL_BASE_URL="https://api.deepseek.com"
export COPRODUCT_MODEL_CHAT_MODEL="deepseek-chat"
```


## Auth

Use header:

```text
Authorization: Bearer dev-token
```
