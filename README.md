# 🇵🇹 Portugal Taxes

> Portuguese IRS (income tax) calculator for residents, non-residents, and NHR — covering fiscal years 2023–2025.

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/ci.yml/badge.svg)](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/ci.yml)
[![PythonAnywhere](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/pa-deploy.yml/badge.svg)](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/pa-deploy.yml)
[![Fly.io](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/fly-deploy.yml/badge.svg)](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/fly-deploy.yml)

---

## Features

- **Progressive IRS tax** with official 2023–2025 brackets for Mainland, Madeira, and Azores
- **Residence types**: resident (`r`), non-resident flat 25% (`nr`), non-habitual resident flat 20% (`nhr`)
- **Category A** (employee) and **Category B** (independent / ENI) with 75% coefficient and year 1/2 startup discounts
- **Social security** for both categories, including the 12-month exemption for new Category B activity
- **Family quotient** — joint declarations, per-child deductions, under-3 bonus
- **Solidarity tax** for residents above €75 000
- **Web app** — multi-user, saves calculation history, shows alternative scenarios (NHR / joint / single / no-kids)
- **CLI** — single-command calculation for quick lookups
- **Docker** — one-line production-grade deployment via Gunicorn

---

## Quick start

### Web app (local)

```bash
git clone https://github.com/NPodlozhniy/portugal-taxes.git
cd portugal-taxes
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000
```

### CLI

```bash
pip install -r requirements.txt

python main.py -a 50000                         # Category A, resident, Mainland
python main.py -a -nr 15000                     # Non-resident
python main.py -ar Madeira 50000                # Resident, Madeira
python main.py 60000 --year 2024 -nhr Mainland -b 04/23 -e 344.16
python main.py --help
```

---


## Docker

```bash
docker build -t portugal-taxes .
docker run -p 5000:5000 -e SECRET_KEY=changeme portugal-taxes
# → http://localhost:5000
```

---

## Configuration

The app reads these environment variables at runtime:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `devsecret` | Flask session signing key — **change in production** |
| `FLASK_DEBUG` | `false` | Set `true` for hot-reload during development |

Copy `.env.example` to `.env` for local overrides (never commit `.env`).

---

## Running tests

```bash
pip install -r requirements-dev.txt
pytest --cov --cov-report=term-missing
```

Current coverage: **91%** (model 99%, app routes 90%).

---

## Deployment

### PythonAnywhere (recommended — free tier, persistent SQLite)

1. Create a free [PythonAnywhere](https://www.pythonanywhere.com) account (Beginner plan).
2. Open a **Bash console** and run:
   ```bash
   git clone https://github.com/NPodlozhniy/portugal-taxes.git
   cd portugal-taxes
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python -c "from app import db, app; app.app_context().push(); db.create_all()"
   ```
3. Go to **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.11**.
4. Set:
   - **Source code**: `/home/<username>/portugal-taxes`
   - **Virtualenv**: `/home/<username>/portugal-taxes/.venv`
5. Edit the **WSGI file** — replace its contents with:
   ```python
   import sys
   sys.path.insert(0, '/home/<username>/portugal-taxes')
   from app import app as application
   ```
6. Add **environment variable** `SECRET_KEY` (a long random string) in the Web tab.
7. Click **Reload** — your app is live at `<username>.pythonanywhere.com`.

> The SQLite database lives at `~/portugal-taxes/taxes.db` and persists across deploys.
> To deploy updates: `git pull` in the Bash console, then Reload.
> Free accounts require a once-per-3-months renewal (one-click from the dashboard).

#### CI/CD auto-deploy (optional)

Push to `master` → GitHub Actions pulls the latest code and reloads PythonAnywhere automatically.

**How it works:** The app exposes a `POST /deploy` endpoint that runs `git pull`. GitHub Actions calls it, then hits the PythonAnywhere API to reload the web app. No SSH required — works on the free Beginner plan.

> **Note:** PythonAnywhere free tier does not allow inbound SSH from external hosts, so SSH-based deploy (e.g. `appleboy/ssh-action`) will fail with exit code 254. The webhook approach below is the correct alternative.

**One-time setup:**

1. Generate a random deploy token:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Add it to your PythonAnywhere **WSGI file** (Web tab → WSGI file link), before the `from app import` line:
   ```python
   import os
   os.environ['DEPLOY_TOKEN'] = 'your-token-here'
   os.environ['SECRET_KEY'] = 'your-secret-key-here'
   ```
3. Get your PythonAnywhere API token: **Account** tab → **API token** → Create.
4. Add two secrets to your GitHub repo (**Settings → Secrets and variables → Actions**):
   - `DEPLOY_TOKEN` — same token from step 1
   - `PYTHONANYWHERE_API_TOKEN` — token from step 3

After pushing to `master`, the **PythonAnywhere** badge will turn green.

### Fly.io

```bash
# Install flyctl, then:
fly launch          # detects Dockerfile, creates fly.toml
fly secrets set SECRET_KEY=<random>
fly volumes create portugal_data --size 1 --region lhr
fly deploy
```

Add to `fly.toml`:
```toml
[mounts]
  source = "portugal_data"
  destination = "/data"
```

### VPS / any Docker host

```bash
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=<random> \
  -v /data/portugal-taxes:/home/instance \
  --restart unless-stopped \
  portugal-taxes
```

Put Nginx in front as a reverse proxy and add a TLS certificate via Certbot.

---

## Architecture

```
model.py      Core Income class — all tax logic (no I/O)
config.py     Loads rates.json → brackets, IAS per year/region
rates.json    Tax brackets & rates for 2023–2025
app.py        Flask web app (User + Calculation models, SQLite)
main.py       CLI front-end (argparse)
tests/        pytest suite — model unit tests + Flask route integration tests
```

---

## Domain notes

| Term | Meaning |
|---|---|
| **IAS** | Indexante de Apoios Sociais — reference value used for deduction floors |
| **Specific deduction** | `8.54 × IAS` for Cat A; reduces taxable base before progressive tax |
| **75% coefficient** | Cat B: only 75% of gross income is taxable before SS/deductions |
| **NHR** | Non-Habitual Resident regime — flat 20% on PT-source employment income |
| **Solidarity tax** | Extra 2.5–5% for residents earning above €75 000 |

---

## License

[MIT](LICENSE) © Nikita Podlozhniy
