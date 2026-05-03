# utils/bcv.py
import logging
from django.core.cache import cache
from decimal import Decimal

logger = logging.getLogger(__name__)

# Intentar importar bcv_exchange
try:
    from bcv_exchange import get_exchange_rate as get_bcv_rate
    BCV_AVAILABLE = True
except ImportError:
    BCV_AVAILABLE = False
    logger.warning("bcv_exchange no está instalado. Usando tasa de respaldo.")


def get_usd_rate():
    """
    Obtiene la tasa oficial USD/BS del BCV.
    Usa cache de 1 hora para evitar muchas consultas.
    """
    cache_key = 'bcv_usd_rate'
    rate = cache.get(cache_key)
    
    if rate is None:
        if BCV_AVAILABLE:
            try:
                exchange_data = get_bcv_rate()
                # La estructura puede variar, adaptar según la respuesta real
                if isinstance(exchange_data, dict):
                    rate = exchange_data.get('exchange_rates', {}).get('USD')
                    if not rate:
                        rate = exchange_data.get('USD')
                elif isinstance(exchange_data, (int, float, Decimal)):
                    rate = exchange_data
                else:
                    rate = Decimal('36.50')  # Tasa de respaldo
                
                rate = Decimal(str(rate))
                cache.set(cache_key, rate, 3600)
                logger.info(f"Tasa USD/BS actualizada: {rate}")
            except Exception as e:
                logger.error(f"Error obteniendo tasa BCV: {e}")
                rate = cache.get(cache_key) or Decimal('36.50')
        else:
            rate = Decimal('36.50')
    
    return rate


def get_rates():
    """Obtiene todas las tasas disponibles"""
    if BCV_AVAILABLE:
        try:
            return get_bcv_rate()
        except Exception as e:
            logger.error(f"Error obteniendo tasas BCV: {e}")
    return None