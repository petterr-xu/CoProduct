# CoProduct Frontend

## Run

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

or if you run service on dev-env:
```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use 20
npm install
cp .env.example .env.local
npm run dev

```
## Env

- `NEXT_PUBLIC_API_BASE_URL`: backend base url
