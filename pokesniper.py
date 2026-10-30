
import os
import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
PRODUCTS_FILE = ROOT / "config" / "products.json"
STATE_FILE = ROOT / "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 PokeSniperMonitor/1.0"
}

AVAILABLE = [
    "add to cart",
    "add for shipping",
    "in stock",
    "available now",
    "ship it"
]

UNAVAILABLE = [
    "out of stock",
    "sold out",
    "currently unavailable",
    "temporarily unavailable"
]


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def notify(message, url):
    topic = os.getenv("NTFY_TOPIC")

    if not topic:
        print("Missing NTFY_TOPIC secret.")
        return

    response = requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode(),
        headers={
            "Title": "POKESNIPER DROP ALERT",
            "Priority": "urgent",
            "Click": url
        },
        timeout=20
    )
    response.raise_for_status()
    print("iPhone alert sent!")


def check_product(product):
    url = product["url"]

    if not url.startswith("https://"):
        return "unknown"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        page = soup.get_text(" ", strip=True).lower()

        if len(page) < 100:
            return "unknown"

        if any(word in page for word in UNAVAILABLE):
            return "unavailable"

        if any(word in page for word in AVAILABLE):
            return "available"

        return "unknown"

    except requests.RequestException as error:
        print(f"Could not check {url}: {error}")
        return "unknown"


def main():
    products = load_json(PRODUCTS_FILE, [])
    state = load_json(STATE_FILE, {})

    for product in products:
        name = product["name"]
        store = product["store"]
        url = product["url"]

        print(f"Checking {store}: {name}")

        status = check_product(product)
        previous = state.get(url, "unknown")

        print(f"Availability: {status}")

        if status == "available" and previous != "available":
            message = (
                f"POKEMON CARD DROP!\n"
                f"Product: {name}\n"
                f"Store: {store}\n"
                f"Buy/check here: {url}"
            )

            notify(message, url)

        if status != "unknown":
            state[url] = status

        time.sleep(5)

    save_state(state)


if __name__ == "__main__":
    main()
