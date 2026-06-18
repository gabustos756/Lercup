"""Google Maps link helpers — no paid API keys required."""

from urllib.parse import quote
from typing import Optional, Tuple


def google_maps_search_url(label: str) -> str:
    """Free Google Maps search link (no API key)."""
    if not label or not str(label).strip():
        return ""
    q = quote(str(label).strip())
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def is_google_maps_url(url: str) -> bool:
    if not url:
        return False
    lower = url.lower()
    return "google.com/maps" in lower or "maps.google.com" in lower or "goo.gl/maps" in lower


def normalize_location_fields(
    label: Optional[str],
    url: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (label, url). Keeps a pasted Google Maps link; otherwise builds search URL from label.
    """
    clean_label = label.strip() if label and label.strip() else None
    clean_url = url.strip() if url and url.strip() else None

    if clean_url and is_google_maps_url(clean_url):
        return clean_label, clean_url

    if clean_label:
        return clean_label, google_maps_search_url(clean_label)

    return clean_label, clean_url


def map_search_url(label: str, provider: str = "google") -> str:
    """Jinja filter — Google Maps search from place name."""
    return google_maps_search_url(label)
