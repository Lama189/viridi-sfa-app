# Viridi market

Telegram bot and Mini App for Viridi clients.

## Configuration

Configure these variables before running the bot or deploying the Mini App:

- `TELEGRAM_BOT_TOKEN` — token shared by the bot and FastAPI `telegram-login` validation;
- `VIRIDI_API_URL` — FastAPI origin for the bot, without `/api/v1`;
- `TELEGRAM_WEB_APP_URL` — public HTTPS URL of the deployed Mini App;
- `VITE_API_URL` — FastAPI API URL for the Mini App, including `/api/v1`.

Telegram requires an HTTPS URL for `TELEGRAM_WEB_APP_URL`.

## Run locally

```bash
cd telegram_bot
npm run dev
```

```bash
TELEGRAM_BOT_TOKEN=... VIRIDI_API_URL=http://localhost:8000 TELEGRAM_WEB_APP_URL=https://... uv run python telegram_bot/bot.py
```

The bot flow is `/start` → activation code → shared phone contact → full name → `POST /api/v1/clients/register` → Mini App button.

## Docker Compose

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEB_APP_URL` in the root `.env`, then start the stack:

```bash
docker compose up --build
```

The `telegram-bot` service waits for the API healthcheck and uses `http://web:8000` inside the Docker network.
