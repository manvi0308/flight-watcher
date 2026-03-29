# ✈️ Flight Price Watcher Bot

Polls Google Flights every 10 minutes and sends a WhatsApp alert when the price
for your chosen route drops below your target threshold.

---

## How it works

```
[SerpAPI / Google Flights] ──► [Python bot] ──► [Twilio] ──► [Your WhatsApp]
        every 10 min             compares price        if price ≤ threshold
```

---

## 1. Get your API keys

### SerpAPI (flight data)
1. Sign up at https://serpapi.com (100 free searches/month)
2. Copy your API key from the dashboard

### Twilio (WhatsApp)
1. Sign up at https://twilio.com
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Follow the sandbox setup — scan the QR code with your phone
4. Note down:
   - Account SID
   - Auth Token
   - Sandbox number (looks like `whatsapp:+14155238886`)

---

## 2. Configure environment variables

```bash
cp .env.example .env
# Fill in your values
```

Key variables:

| Variable | Example | Description |
|---|---|---|
| `FLIGHT_ORIGIN` | `BOM` | Departure airport IATA code |
| `FLIGHT_DESTINATION` | `LHR` | Arrival airport IATA code |
| `FLIGHT_DATE` | `2025-06-15` | Travel date (YYYY-MM-DD) |
| `PRICE_THRESHOLD` | `25000` | Alert when price drops below this |
| `CURRENCY` | `INR` | Currency for prices |
| `POLL_INTERVAL_SECONDS` | `600` | How often to check (600 = 10 min) |

---

## 3. Run locally

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your values
set -a && source .env && set +a   # load env vars (mac/linux)
python bot.py
```

You'll see logs like:
```
2025-03-29 10:00:00 [INFO] ✈️  Flight watcher started | BOM → LHR on 2025-06-15 ...
2025-03-29 10:00:03 [INFO] Cheapest: INR 22450 on Air India
2025-03-29 10:00:03 [INFO] WhatsApp alert sent ✓
```

---

## 4. Deploy to Railway (free, always-on)

Railway runs your bot 24/7 for free on the hobby plan.

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login & init
railway login
railway init         # select "Empty project"
railway link         # link to your project

# Add env vars via dashboard or CLI
railway variables set TWILIO_ACCOUNT_SID=AC...
railway variables set TWILIO_AUTH_TOKEN=...
railway variables set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
railway variables set WHATSAPP_TO=whatsapp:+91...
railway variables set SERPAPI_KEY=...
railway variables set FLIGHT_ORIGIN=BOM
railway variables set FLIGHT_DESTINATION=LHR
railway variables set FLIGHT_DATE=2025-06-15
railway variables set PRICE_THRESHOLD=25000
railway variables set CURRENCY=INR
railway variables set POLL_INTERVAL_SECONDS=600

# Deploy
railway up
```

Railway detects the `Procfile` and runs `python bot.py` as a **worker** (no HTTP port needed).

---

## 5. Alert behaviour

- Alerts fire when `price ≤ PRICE_THRESHOLD`
- A 1-hour cooldown prevents spam — you'll get at most one alert per hour
- A new alert is always sent if the price drops further than the last check

---

## IATA codes quick reference

| City | Code |
|---|---|
| Mumbai | BOM |
| Delhi | DEL |
| Bangalore | BLR |
| Dubai | DXB |
| London Heathrow | LHR |
| Singapore | SIN |
| New York JFK | JFK |
| Bangkok | BKK |

---

## Project structure

```
flight-watcher/
├── bot.py            # main polling loop
├── requirements.txt  # dependencies
├── Procfile          # Railway/Heroku process definition
├── .env.example      # environment variable template
└── README.md         # this file
```
