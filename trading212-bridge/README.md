# WealthDashboard Trading 212 Bridge

A read-only local backend for the WealthDashboard HTML app. Trading 212 credentials stay on the OpenMediaVault host in a private `.env` file and are never sent to the browser.

## Install on OpenMediaVault

1. Create a folder under your configured Compose shared folder, e.g. `/srv/dev-disk-by-uuid-.../compose/wealthdashboard-trading212`.
2. Copy `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `app.py`, and `.env.example` into it.
3. Copy `.env.example` to `.env`; edit the two credential values. Set `T212_ENVIRONMENT=live`.
4. Generate a Trading 212 API key with **read-only** permissions for Portfolio and Account data. Do not enable any order/trading permissions. If Trading 212 offers IP restrictions, restrict it to the server's public IP.
5. Protect the .env file: `chmod 600 .env`. Never commit it or paste its contents into ChatGPT.
6. In the OMV Compose UI, select the folder/project and deploy, or run `docker compose up -d --build` in that directory.
7. Test on the home network: `http://SERVER-IP:8765/health` should return `{"ok":true,...}`.

The API listens on port 8765. The default polling interval is 15 minutes (minimum 5 minutes). The first automatic poll runs after startup plus one interval; use the app's **Jetzt synchronisieren** button for the first import.

## API

- `GET /health`
- `GET /api/status`
- `GET /api/portfolio`
- `POST /api/sync`

SQLite snapshots persist in the Docker named volume `trading212-data`.

## Security notes

- Use a dedicated read-only API key. The bridge only makes GET requests to Trading 212.
- Keep port 8765 reachable only from your trusted LAN. Do not port-forward it to the internet.
- The app is a local HTML file and may be opened with `file://`; the bridge enables CORS for that use. This is intended for trusted home-network use only. For remote access, put it behind authenticated HTTPS (e.g. a VPN/reverse proxy) before exposing it.
- Credentials are only read from the backend container environment. There is no endpoint to retrieve or change them.
