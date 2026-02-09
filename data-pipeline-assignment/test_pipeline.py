#!/usr/bin/env python3
"""
Quick test script to validate pipeline components
Run this to test individual components before running full DAG
"""
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_scraper():
    """Test the web scraper"""
    print("\n=== Testing Web Scraper ===")
    try:
        from scrape_products import scrape_books
        products = scrape_books(max_pages=1)
        print(f"✓ Successfully scraped {len(products)} products")
        if products:
            print(f"Sample: {products[0]}")
        return True
    except Exception as e:
        print(f"✗ Scraper failed: {e}")
        return False


def test_exchange_rate():
    """Test exchange rate API"""
    print("\n=== Testing Exchange Rate API ===")
    try:
        from fetch_exchange_rate import fetch_exchange_rate
        rate = fetch_exchange_rate()
        if rate:
            print(f"✓ Successfully fetched rate: 1 GBP = {rate} INR")
            return True
        else:
            print("✗ Failed to fetch exchange rate")
            return False
    except Exception as e:
        print(f"✗ Exchange rate fetch failed: {e}")
        return False


def test_transformation():
    """Test data transformation"""
    print("\n=== Testing Data Transformation ===")
    try:
        from transform_data import transform_product
        
        sample_product = {
            'title': '  Test Book  ',
            'price_gbp': 25.99,
            'category': 'fiction',
            'availability': 'In stock (15 available)'
        }
        
        transformed = transform_product(sample_product, 105.50)
        
        if transformed:
            print(f"✓ Transformation successful")
            print(f"  Original: {sample_product['title']} @ £{sample_product['price_gbp']}")
            print(f"  Transformed: {transformed['title']} @ ₹{transformed['price_inr']}")
            print(f"  Product ID: {transformed['product_id']}")
            print(f"  Price Tier: {transformed['price_tier']}")
            return True
        else:
            print("✗ Transformation failed")
            return False
    except Exception as e:
        print(f"✗ Transformation failed: {e}")
        return False


def test_database_connection():
    """Test database connectivity"""
    print("\n=== Testing Database Connection ===")
    try:
        import psycopg2
        
        db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'database': os.getenv('POSTGRES_DB', 'pipeline_db'),
            'user': os.getenv('POSTGRES_USER', 'pipeline_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'pipeline_pass')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test table existence
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['staging_exchange_rates', 'products', 'raw_products']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if not missing_tables:
            print(f"✓ Database connected successfully")
            print(f"  Found tables: {', '.join(tables)}")
        else:
            print(f"⚠ Connected but missing tables: {', '.join(missing_tables)}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("  Make sure PostgreSQL is running and accessible")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATA PIPELINE VALIDATION TESTS")
    print("=" * 60)
    
    results = {
        'Scraper': test_scraper(),
        'Exchange Rate API': test_exchange_rate(),
        'Transformation': test_transformation(),
        'Database': test_database_connection()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{component:20s} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    
    if all_passed:
        print("✓ All tests passed! Pipeline is ready to run.")
        return 0
    else:
        print("✗ Some tests failed. Please fix issues before running pipeline.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
