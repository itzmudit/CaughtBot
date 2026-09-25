"""
A small per-model token rate limiter, so we stay under Groq's free-tier
tokens-per-minute (TPM) limits instead of crashing with a 429.

How it works: we keep a rolling 60-second window of how many tokens each model
has used. Before a call we wait until there's room in the budget; after a call
we record the tokens actually used (from response.usage). This paces requests
smoothly instead of blasting the API and getting rate-limited.
"""
import threading
import time

_WINDOW = 60.0          # seconds
_LOCK = threading.Lock()
_usage: dict[str, list[tuple[float, int]]] = {}


def wait_for(model: str, budget: int = 7000, est: int = 1000) -> None:
    """Block until sending an ~`est`-token request keeps this model under `budget` TPM."""
    while True:
        with _LOCK:
            now = time.time()
            window = _usage.setdefault(model, [])
            while window and now - window[0][0] > _WINDOW:
                window.pop(0)
            used = sum(t for _, t in window)
            if used + est <= budget or not window:
                return
            sleep_for = _WINDOW - (now - window[0][0]) + 0.2
        time.sleep(min(max(sleep_for, 0.2), 6.0))


def record(model: str, tokens: int) -> None:
    """Record tokens actually spent on `model` (call after each request)."""
    with _LOCK:
        _usage.setdefault(model, []).append((time.time(), tokens))
