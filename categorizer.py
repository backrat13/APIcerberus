'''python
KNOWN_PORTS = {
    # Development Servers
    3000: ("Development", "React/Node.js dev server"),
    8000: ("Development", "Python/Django dev server"),
    8080: ("Development", "General purpose dev server"),
    5000: ("Development", "Flask dev server"),
    4200: ("Development", "Angular dev server"),
    5173: ("Development", "Vite dev server"),

    # Common Public Services
    80: ("Web Server", "Standard HTTP"),
    443: ("Web Server", "Standard HTTPS"),
    22: ("Remote Access", "SSH"),

    # Databases
    5432: ("Database", "PostgreSQL"),
    3306: ("Database", "MySQL/MariaDB"),
    27017: ("Database", "MongoDB"),
    6379: ("Database", "Redis"),
}

SUSPICIOUS_NAMES = ["telemetry", "tracker", "metrics"]

def categorize_api(api_info):
    """
    Categorizes an API based on its port, name, and address.
    Returns a category, a description, and a suspicion flag.
    """
    port = api_info.get('port')
    name = api_info.get('name', '').lower()
    address = api_info.get('address', '')

    category = "Unknown"
    description = "No specific information available."
    is_suspicious = False

    # Rule 1: Check known ports
    if port in KNOWN_PORTS:
        category, description = KNOWN_PORTS[port]

    # Rule 2: Check for suspicious names
    if any(susp_name in name for susp_name in SUSPICIOUS_NAMES):
        is_suspicious = True
        description += " Contains a suspicious keyword in its name."

    # Rule 3: Non-localhost listeners might be suspicious
    if address not in ('127.0.0.1', '::1', '0.0.0.0') and not is_suspicious:
        is_suspicious = True
        description = f"Listening on a public IP ({address}). Verify this is intended."
        if category == "Unknown":
            category = "Public-Facing"

    # Rule 4: High, unassigned ports can be suspicious
    if category == "Unknown" and port > 1024:
        description = "Listening on a high, unassigned port."

    return category, description, is_suspicious
