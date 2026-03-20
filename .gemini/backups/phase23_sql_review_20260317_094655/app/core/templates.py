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

templates.env.filters["currency"] = currency_filter

# Add more filters here if needed
