"""
Daily Product Pricing Intelligence Pipeline
Orchestrates scraping, exchange rate fetching, transformation, and loading
"""
import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Add scripts directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scrape_products import scrape_books
from fetch_exchange_rate import fetch_exchange_rate, store_exchange_rate, get_latest_exchange_rate
from transform_data import transform_products
from load_data import load_products_replace, load_raw_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'database': os.getenv('POSTGRES_DB', 'pipeline_db'),
    'user': os.getenv('POSTGRES_USER', 'pipeline_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pipeline_pass')
}

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30)
}


def scrape_products_task(**context):
    """
    Task 1: Scrape product data from books.toscrape.com
    """
    logger.info("Starting product scraping...")
    
    try:
        products = scrape_books(max_pages=5)
        
        if not products:
            raise ValueError("No products were scraped")
        
        logger.info(f"Successfully scraped {len(products)} products")
        
        # Optionally store raw products
        if load_raw_products(products, DB_CONFIG):
            logger.info("Raw products stored in database")
        
        # Push to XCom for next tasks
        context['ti'].xcom_push(key='raw_products', value=products)
        
        return len(products)
        
    except Exception as e:
        logger.error(f"Error in scrape_products_task: {e}")
        raise


def fetch_and_store_exchange_rate_task(**context):
    """
    Task 2: Fetch GBP to INR exchange rate and store in staging table
    """
    logger.info("Fetching exchange rate...")
    
    try:
        # Fetch exchange rate
        exchange_rate = fetch_exchange_rate(base_currency='GBP', target_currency='INR')
        
        if not exchange_rate:
            raise ValueError("Failed to fetch exchange rate")
        
        # Store in database
        if not store_exchange_rate(exchange_rate, DB_CONFIG, 'GBP', 'INR'):
            raise ValueError("Failed to store exchange rate")
        
        logger.info(f"Exchange rate stored: 1 GBP = {exchange_rate} INR")
        
        # Push to XCom
        context['ti'].xcom_push(key='exchange_rate', value=exchange_rate)
        
        return exchange_rate
        
    except Exception as e:
        logger.error(f"Error in fetch_and_store_exchange_rate_task: {e}")
        raise


def transform_products_task(**context):
    """
    Task 3: Transform raw products using exchange rate from staging
    """
    logger.info("Transforming products...")
    
    try:
        # Pull raw products from XCom
        ti = context['ti']
        raw_products = ti.xcom_pull(key='raw_products', task_ids='scrape_products')
        
        if not raw_products:
            raise ValueError("No raw products found in XCom")
        
        # Get exchange rate from staging table (most reliable)
        exchange_rate = get_latest_exchange_rate(DB_CONFIG)
        
        if not exchange_rate:
            # Fallback to XCom if staging table fails
            logger.warning("Could not retrieve from staging, using XCom")
            exchange_rate = ti.xcom_pull(key='exchange_rate', task_ids='fetch_exchange_rate')
        
        if not exchange_rate:
            raise ValueError("No exchange rate available")
        
        # Transform products
        transformed_products = transform_products(raw_products, exchange_rate)
        
        if not transformed_products:
            raise ValueError("No products were transformed")
        
        logger.info(f"Successfully transformed {len(transformed_products)} products")
        
        # Push to XCom
        ti.xcom_push(key='transformed_products', value=transformed_products)
        
        return len(transformed_products)
        
    except Exception as e:
        logger.error(f"Error in transform_products_task: {e}")
        raise


def load_products_task(**context):
    """
    Task 4: Load transformed products into final products table
    """
    logger.info("Loading products to database...")
    
    try:
        # Pull transformed products from XCom
        ti = context['ti']
        transformed_products = ti.xcom_pull(key='transformed_products', task_ids='transform_products')
        
        if not transformed_products:
            raise ValueError("No transformed products found in XCom")
        
        # Load products (using REPLACE strategy for full refresh)
        if not load_products_replace(transformed_products, DB_CONFIG):
            raise ValueError("Failed to load products")
        
        logger.info(f"Successfully loaded {len(transformed_products)} products")
        
        return len(transformed_products)
        
    except Exception as e:
        logger.error(f"Error in load_products_task: {e}")
        raise


# Define the DAG
with DAG(
    dag_id='product_pricing_pipeline',
    default_args=default_args,
    description='Daily pipeline for scraping product data and pricing intelligence',
    schedule_interval='@daily',  # Run daily
    start_date=days_ago(1),
    catchup=False,
    tags=['pricing', 'etl', 'web-scraping']
) as dag:
    
    # Task 1: Scrape products
    scrape_task = PythonOperator(
        task_id='scrape_products',
        python_callable=scrape_products_task,
        provide_context=True
    )
    
    # Task 2: Fetch and store exchange rate
    exchange_rate_task = PythonOperator(
        task_id='fetch_exchange_rate',
        python_callable=fetch_and_store_exchange_rate_task,
        provide_context=True
    )
    
    # Task 3: Transform products
    transform_task = PythonOperator(
        task_id='transform_products',
        python_callable=transform_products_task,
        provide_context=True
    )
    
    # Task 4: Load products to database
    load_task = PythonOperator(
        task_id='load_products',
        python_callable=load_products_task,
        provide_context=True
    )
    
    # Define task dependencies
    # Scraping and exchange rate fetching can run in parallel
    # Transformation needs both to complete
    # Loading needs transformation to complete
    [scrape_task, exchange_rate_task] >> transform_task >> load_task
