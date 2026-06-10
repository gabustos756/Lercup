from datetime import datetime

_WEEKDAYS_ES = (
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo",
)
_MONTHS_ES = (
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
)


def format_match_datetime(dt: datetime) -> str:
    """Format datetime as 'Lunes 15 Jun, 18:00'."""
    if dt is None:
        return ""
    weekday = _WEEKDAYS_ES[dt.weekday()]
    month = _MONTHS_ES[dt.month - 1]
    return f"{weekday} {dt.day} {month}, {dt.strftime('%H:%M')}"


def time_ago(dt: datetime) -> str:
    """Return a human-readable relative time string in Spanish."""
    if dt is None:
        return ""

    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return "ahora"
    if seconds < 45:
        return "hace un momento"
    if seconds < 90:
        return "hace 1 min"
    minutes = seconds // 60
    if minutes < 45:
        return f"hace {minutes} min"
    if minutes < 90:
        return "hace 1 hora"
    hours = minutes // 60
    if hours < 24:
        return f"hace {hours} horas" if hours > 1 else "hace 1 hora"
    if hours < 36:
        return "hace 1 día"
    days = hours // 24
    if days < 7:
        return f"hace {days} días" if days > 1 else "hace 1 día"
    if days < 14:
        return "hace 1 semana"
    weeks = days // 7
    if weeks < 5:
        return f"hace {weeks} semanas" if weeks > 1 else "hace 1 semana"
    return dt.strftime("%d/%m/%Y")
