"""
Fetch GBP to INR exchange rate from public API
Store in PostgreSQL staging table
"""
import logging
from datetime import date
from typing import Optional, Dict
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_exchange_rate(
    base_currency: str = "GBP",
    target_currency: str = "INR",
    api_url: str = "https://api.exchangerate.host/latest"
) -> Optional[float]:
    """
    Fetch exchange rate from exchangerate.host API
    
    Args:
        base_currency: Base currency code (default: GBP)
        target_currency: Target currency code (default: INR)
        api_url: API endpoint URL
        
    Returns:
        Exchange rate as float, or None if failed
    """
    try:
        params = {
            'base': base_currency,
            'symbols': target_currency
        }
        
        logger.info(f"Fetching exchange rate: {base_currency} -> {target_currency}")
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success', True):
            logger.error(f"API returned error: {data}")
            return None
        
        rates = data.get('rates', {})
        exchange_rate = rates.get(target_currency)
        
        if exchange_rate:
            logger.info(f"Exchange rate fetched: 1 {base_currency} = {exchange_rate} {target_currency}")
            return float(exchange_rate)
        else:
            logger.error(f"Exchange rate not found in response: {data}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error fetching exchange rate: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def store_exchange_rate(
    exchange_rate: float,
    db_config: Dict,
    base_currency: str = "GBP",
    target_currency: str = "INR"
) -> bool:
    """
    Store exchange rate in PostgreSQL staging table
    
    Args:
        exchange_rate: The exchange rate value
        db_config: Database connection configuration
        base_currency: Base currency code
        target_currency: Target currency code
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        today = date.today()
        
        # Upsert exchange rate for today
        insert_query = """
            INSERT INTO staging_exchange_rates (date, base_currency, target_currency, exchange_rate)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date, base_currency, target_currency)
            DO UPDATE SET 
                exchange_rate = EXCLUDED.exchange_rate,
                fetched_at = CURRENT_TIMESTAMP
        """
        
        cursor.execute(insert_query, (today, base_currency, target_currency, exchange_rate))
        conn.commit()
        
        logger.info(f"Exchange rate stored successfully for {today}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error storing exchange rate: {e}")
        return False


def get_latest_exchange_rate(db_config: Dict) -> Optional[float]:
    """
    Retrieve the latest exchange rate from staging table
    
    Args:
        db_config: Database connection configuration
        
    Returns:
        Latest exchange rate or None
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT exchange_rate, date
            FROM staging_exchange_rates
            ORDER BY date DESC
            LIMIT 1
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"Retrieved exchange rate: {result['exchange_rate']} (date: {result['date']})")
            return float(result['exchange_rate'])
        else:
            logger.warning("No exchange rate found in staging table")
            return None
            
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving exchange rate: {e}")
        return None


if __name__ == "__main__":
    # Test the exchange rate fetcher
    rate = fetch_exchange_rate()
    if rate:
        print(f"Current GBP to INR rate: {rate}")
