import random
import string
from datetime import datetime

def generate_radicado() -> str:
    """Generar número de radicado único"""
    year = datetime.now().year
    # Generar código alfanumérico de 6 caracteres
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{year}-{code}"

def format_date(date: datetime) -> str:
    """Formatear fecha para mostrar"""
    if date:
        return date.strftime("%d/%m/%Y %H:%M")
    return ""