
import os
import requests

topic = os.environ["NTFY_TOPIC"]

response = requests.post(
    f"https://ntfy.sh/{topic}",
    data="PokéSniper is connected! Your iPhone alerts are working.",
    headers={
        "Title": "PokéSniper Test",
        "Priority": "high"
    },
    timeout=20
)

response.raise_for_status()
print("Test notification sent!")
