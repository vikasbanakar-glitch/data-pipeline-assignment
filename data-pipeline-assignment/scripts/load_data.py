"""
Load transformed product data into PostgreSQL
Supports both replace and upsert strategies
"""
import logging
from typing import List, Dict
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_products_replace(products: List[Dict], db_config: Dict) -> bool:
    """
    Load products using REPLACE strategy (truncate and insert)
    
    Args:
        products: List of transformed product dictionaries
        db_config: Database connection configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Truncate the products table
        logger.info("Truncating products table...")
        cursor.execute("TRUNCATE TABLE products")
        
        # Prepare data for bulk insert
        insert_query = """
            INSERT INTO products (
                product_id, title, price_gbp, price_inr, category,
                availability_status, stock_quantity, price_tier
            )
            VALUES %s
        """
        
        # Convert products to tuples
        values = [
            (
                p['product_id'],
                p['title'],
                p['price_gbp'],
                p['price_inr'],
                p['category'],
                p['availability_status'],
                p['stock_quantity'],
                p['price_tier']
            )
            for p in products
        ]
        
        # Bulk insert
        execute_values(cursor, insert_query, values)
        
        conn.commit()
        logger.info(f"Successfully loaded {len(products)} products (REPLACE mode)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading products: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_products_upsert(products: List[Dict], db_config: Dict) -> bool:
    """
    Load products using UPSERT strategy (insert or update on conflict)
    
    Args:
        products: List of transformed product dictionaries
        db_config: Database connection configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        upsert_query = """
            INSERT INTO products (
                product_id, title, price_gbp, price_inr, category,
                availability_status, stock_quantity, price_tier
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                price_gbp = EXCLUDED.price_gbp,
                price_inr = EXCLUDED.price_inr,
                category = EXCLUDED.category,
                availability_status = EXCLUDED.availability_status,
                stock_quantity = EXCLUDED.stock_quantity,
                price_tier = EXCLUDED.price_tier,
                updated_at = CURRENT_TIMESTAMP
        """
        
        # Execute upsert for each product
        for product in products:
            cursor.execute(upsert_query, (
                product['product_id'],
                product['title'],
                product['price_gbp'],
                product['price_inr'],
                product['category'],
                product['availability_status'],
                product['stock_quantity'],
                product['price_tier']
            ))
        
        conn.commit()
        logger.info(f"Successfully upserted {len(products)} products")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error upserting products: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_raw_products(products: List[Dict], db_config: Dict) -> bool:
    """
    Load raw (untransformed) products to raw_products table
    Optional intermediate step for debugging
    
    Args:
        products: List of raw product dictionaries
        db_config: Database connection configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Truncate raw_products table
        cursor.execute("TRUNCATE TABLE raw_products")
        
        insert_query = """
            INSERT INTO raw_products (title, price_gbp, category, availability)
            VALUES %s
        """
        
        values = [
            (
                p.get('title'),
                p.get('price_gbp'),
                p.get('category'),
                p.get('availability')
            )
            for p in products
        ]
        
        execute_values(cursor, insert_query, values)
        
        conn.commit()
        logger.info(f"Successfully loaded {len(products)} raw products")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading raw products: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Test with sample data
    sample_products = [
        {
            'product_id': 'abc123',
            'title': 'Test Book',
            'price_gbp': 25.50,
            'price_inr': 2689.75,
            'category': 'Fiction',
            'availability_status': 'In Stock',
            'stock_quantity': 10,
            'price_tier': 'moderate'
        }
    ]
    
    print("Sample data ready for loading")
