import os
import time
import logging
import requests
from twilio.rest import Client
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Config ────────────────────────────────────────────────────────────────────
TWILIO_SID      = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_TOKEN    = os.environ["TWILIO_AUTH_TOKEN"]
FROM_NUMBER     = os.environ["TWILIO_WHATSAPP_FROM"]   # e.g. whatsapp:+14155238886
TO_NUMBER       = os.environ["WHATSAPP_TO"]            # e.g. whatsapp:+919876543210
SERPAPI_KEY     = os.environ["SERPAPI_KEY"]

ORIGIN          = os.environ.get("FLIGHT_ORIGIN", "BOM")       # IATA code
DESTINATION     = os.environ.get("FLIGHT_DESTINATION", "DXB")
TRAVEL_DATE     = os.environ.get("FLIGHT_DATE", "2025-06-15")  # YYYY-MM-DD
CURRENCY        = os.environ.get("CURRENCY", "INR")
PRICE_THRESHOLD = float(os.environ.get("PRICE_THRESHOLD", 8000))  # alert below this

POLL_EVERY      = int(os.environ.get("POLL_INTERVAL_SECONDS", 600))  # 10 min default

# ── Fetch Prices ──────────────────────────────────────────────────────────────

def fetch_cheapest_flight() -> dict | None:
    """Query SerpAPI Google Flights for the cheapest one-way fare."""
    params = {
        "engine":           "google_flights",
        "departure_id":     ORIGIN,
        "arrival_id":       DESTINATION,
        "outbound_date":    TRAVEL_DATE,
        "currency":         CURRENCY,
        "hl":               "en",
        "type":             "2",          # 1 = round-trip, 2 = one-way
        "api_key":          SERPAPI_KEY,
    }

    resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    best_flights = data.get("best_flights", []) or data.get("other_flights", [])
    if not best_flights:
        logging.warning("No flights found in response.")
        return None

    # Each entry in best_flights has a 'price' key (total for the itinerary)
    cheapest = min(best_flights, key=lambda f: f.get("price", float("inf")))
    flight_info = cheapest.get("flights", [{}])[0]

    return {
        "price":     cheapest.get("price"),
        "airline":   flight_info.get("airline", "Unknown"),
        "departure": flight_info.get("departure_airport", {}).get("time", ""),
        "arrival":   flight_info.get("arrival_airport", {}).get("time", ""),
        "duration":  cheapest.get("total_duration", 0),
    }

# ── WhatsApp Alert ─────────────────────────────────────────────────────────────

def send_whatsapp(flight: dict, prev_price: float | None) -> None:
    hrs, mins = divmod(flight["duration"], 60)
    price_line = f"💸 *{CURRENCY} {flight['price']:,.0f}*"
    if prev_price:
        diff = prev_price - flight["price"]
        price_line += f"  (↓ {CURRENCY} {diff:,.0f} cheaper than last check)"

    body = (
        f"✈️ *Flight Price Alert!*\n"
        f"{ORIGIN} → {DESTINATION}  |  {TRAVEL_DATE}\n"
        f"─────────────────────\n"
        f"{price_line}\n"
        f"🛫 Airline:    {flight['airline']}\n"
        f"🕐 Departs:   {flight['departure']}\n"
        f"🕔 Arrives:   {flight['arrival']}\n"
        f"⏱  Duration:  {hrs}h {mins}m\n"
        f"─────────────────────\n"
        f"🔔 Threshold: {CURRENCY} {PRICE_THRESHOLD:,.0f}\n"
        f"📡 Polled at: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
    )

    Client(TWILIO_SID, TWILIO_TOKEN).messages.create(
        from_=FROM_NUMBER,
        to=TO_NUMBER,
        body=body,
    )
    logging.info("WhatsApp alert sent ✓")

# ── Main Loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    logging.info(
        "✈️  Flight watcher started | %s → %s on %s | threshold %s %s | every %ds",
        ORIGIN, DESTINATION, TRAVEL_DATE, CURRENCY, PRICE_THRESHOLD, POLL_EVERY,
    )

    last_price: float | None = None
    alert_sent_at: float | None = None
    COOLDOWN = 3600  # don't re-alert more than once per hour for the same price

    while True:
        try:
            flight = fetch_cheapest_flight()
            if flight is None:
                time.sleep(POLL_EVERY)
                continue

            price = flight["price"]
            logging.info("Cheapest: %s %s on %s", CURRENCY, price, flight["airline"])

            now = time.time()
            cooldown_over = alert_sent_at is None or (now - alert_sent_at) > COOLDOWN
            price_dropped = last_price is None or price < last_price

            if price <= PRICE_THRESHOLD and (price_dropped or cooldown_over):
                send_whatsapp(flight, last_price)
                alert_sent_at = now

            last_price = price

        except Exception as exc:
            logging.error("Error: %s", exc)

        time.sleep(POLL_EVERY)


if __name__ == "__main__":
    main()
