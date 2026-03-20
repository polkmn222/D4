from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")

def currency_filter(value):
    try:
        if value is None: return "₩ 0"
        return f"₩ {int(value):,}"
    except (ValueError, TypeError):
        return f"₩ {value}"

def datetime_format(value, format="%Y. %-m. %-d. %p %I:%M"):
    if value is None:
        return "N/A"
    from datetime import datetime
    if isinstance(value, datetime):
        return value.strftime(format)
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except ValueError:
            return value
    return str(value)

templates.env.filters["currency"] = currency_filter
templates.env.filters["datetime_format"] = datetime_format

# Add more filters here if needed
