"""
Configuration module for the data pipeline
Centralizes all configuration settings
"""
import os
from typing import Dict


class Config:
    """Pipeline configuration settings"""
    
    # Database Configuration
    DB_CONFIG: Dict[str, any] = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'pipeline_db'),
        'user': os.getenv('POSTGRES_USER', 'pipeline_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pipeline_pass')
    }
    
    # Scraping Configuration
    SCRAPING_CONFIG = {
        'base_url': os.getenv('BASE_SCRAPING_URL', 'https://books.toscrape.com'),
        'max_pages': int(os.getenv('MAX_PAGES_TO_SCRAPE', 5)),
        'timeout': 10,  # seconds
        'user_agent': 'Mozilla/5.0 (compatible; DataPipeline/1.0)'
    }
    
    # Exchange Rate API Configuration
    EXCHANGE_RATE_CONFIG = {
        'api_url': os.getenv('EXCHANGE_RATE_API_URL', 'https://api.exchangerate.host/latest'),
        'base_currency': 'GBP',
        'target_currency': 'INR',
        'timeout': 10  # seconds
    }
    
    # Price Tier Thresholds (in GBP)
    PRICE_TIERS = {
        'cheap': (0, 20),
        'moderate': (20, 50),
        'expensive': (50, float('inf'))
    }
    
    # Loading Strategy
    LOAD_STRATEGY = os.getenv('LOAD_STRATEGY', 'replace')  # 'replace' or 'upsert'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_db_config(cls) -> Dict:
        """Get database configuration"""
        return cls.DB_CONFIG.copy()
    
    @classmethod
    def get_scraping_config(cls) -> Dict:
        """Get scraping configuration"""
        return cls.SCRAPING_CONFIG.copy()
    
    @classmethod
    def get_exchange_rate_config(cls) -> Dict:
        """Get exchange rate API configuration"""
        return cls.EXCHANGE_RATE_CONFIG.copy()
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all configuration settings"""
        required_env_vars = [
            'POSTGRES_HOST',
            'POSTGRES_DB',
            'POSTGRES_USER',
            'POSTGRES_PASSWORD'
        ]
        
        missing = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
            print("Using default values")
        
        return True


# Validate configuration on import
Config.validate()
