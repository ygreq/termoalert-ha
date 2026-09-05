"""Constants for the TermoAlert București integration."""

DOMAIN = "termoalert"

# Configuration keys
CONF_SECTOR = "sector"
CONF_SEARCH_TERM = "search_term"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_SCAN_INTERVAL = 15  # in minutes
DEFAULT_NAME = "TermoAlert"

# Remote source
CMTEB_URL = "https://cmteb.ro/functionare_sistem_termoficare.php"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Device info
MANUFACTURER = "Compania Municipală Termoenergetica București (CMTEB)"
MODEL = "Monitor Sistem Termoficare"

# Platforms
PLATFORMS = ["binary_sensor", "sensor"]
