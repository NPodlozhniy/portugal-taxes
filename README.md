# 🇵🇹 Portugal Taxes

> Portuguese IRS (income tax) calculator for residents, non-residents, and NHR — covering fiscal years 2023–2025.

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/ci.yml/badge.svg)](https://github.com/NPodlozhniy/portugal-taxes/actions/workflows/ci.yml)

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

### Render (recommended — free tier)

1. Push to GitHub.
2. Go to [render.com](https://render.com) → **New → Web Service** → connect your repo.
3. Set:
   - **Runtime**: Docker
   - **Environment variable**: `SECRET_KEY` = a long random string
4. Add a **Disk** (free tier: 1 GB) mounted at `/home/instance` so the SQLite database survives redeploys.
   Update `SQLALCHEMY_DATABASE_URI` in `app.py` to `sqlite:////home/instance/taxes.db` **or** set it via env var.
5. Click **Deploy**.

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
  destination = "/home/instance"
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
