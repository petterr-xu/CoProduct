# CoProduct Backend (M1)

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

## Auth

Use header:

```text
Authorization: Bearer dev-token
```

