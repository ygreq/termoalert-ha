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

# Device info
MANUFACTURER = "Compania Municipală Termoenergetica București (CMTEB)"
MODEL = "Monitor Sistem Termoficare"

# Platforms
PLATFORMS = ["binary_sensor", "sensor"]
