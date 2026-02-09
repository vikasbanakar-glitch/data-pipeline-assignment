"""
Transform raw product data:
- Clean text fields
- Normalize categories
- Parse availability info
- Convert GBP to INR
- Derive price tiers
- Generate stable product IDs
"""
import logging
import hashlib
import re
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and trim text fields
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Trim
    text = text.strip()
    
    return text


def normalize_category(category: str) -> str:
    """
    Normalize category names
    
    Args:
        category: Raw category text
        
    Returns:
        Normalized category
    """
    if not category or category.lower() == 'unknown':
        return 'Uncategorized'
    
    # Clean and capitalize properly
    category = clean_text(category)
    category = category.title()
    
    return category


def parse_availability(availability: str) -> tuple:
    """
    Parse availability text to extract status and quantity
    
    Args:
        availability: Raw availability text (e.g., "In stock (22 available)")
        
    Returns:
        Tuple of (status, quantity)
    """
    if not availability:
        return ('Unknown', None)
    
    availability = clean_text(availability)
    
    # Extract quantity if present
    quantity_match = re.search(r'\((\d+)\s+available\)', availability)
    quantity = int(quantity_match.group(1)) if quantity_match else None
    
    # Determine status
    if 'in stock' in availability.lower():
        status = 'In Stock'
    elif 'out of stock' in availability.lower():
        status = 'Out of Stock'
    else:
        status = 'Unknown'
    
    return (status, quantity)


def convert_price_to_inr(price_gbp: float, exchange_rate: float) -> float:
    """
    Convert GBP price to INR
    
    Args:
        price_gbp: Price in GBP
        exchange_rate: GBP to INR exchange rate
        
    Returns:
        Price in INR (rounded to 2 decimal places)
    """
    if not price_gbp or not exchange_rate:
        return 0.0
    
    price_inr = price_gbp * exchange_rate
    return round(price_inr, 2)


def derive_price_tier(price_gbp: float) -> str:
    """
    Categorize price into tiers
    
    Args:
        price_gbp: Price in GBP
        
    Returns:
        Price tier: 'cheap', 'moderate', or 'expensive'
    """
    if price_gbp < 20:
        return 'cheap'
    elif price_gbp < 50:
        return 'moderate'
    else:
        return 'expensive'


def generate_product_id(title: str, category: str, price_gbp: float) -> str:
    """
    Generate stable product ID by hashing title, category, and price
    
    Args:
        title: Product title
        category: Product category
        price_gbp: Price in GBP
        
    Returns:
        SHA256 hash as product ID
    """
    # Create a unique string from title, category, and price
    unique_string = f"{title}|{category}|{price_gbp}"
    
    # Generate SHA256 hash
    product_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
    
    return product_id


def transform_product(product: Dict, exchange_rate: float) -> Dict:
    """
    Transform a single product with all cleaning and enrichment steps
    
    Args:
        product: Raw product dictionary
        exchange_rate: GBP to INR exchange rate
        
    Returns:
        Transformed product dictionary
    """
    try:
        # Clean text fields
        title = clean_text(product.get('title', ''))
        
        # Normalize category
        category = normalize_category(product.get('category', ''))
        
        # Parse availability
        availability = product.get('availability', '')
        status, quantity = parse_availability(availability)
        
        # Get price
        price_gbp = float(product.get('price_gbp', 0))
        
        # Convert to INR
        price_inr = convert_price_to_inr(price_gbp, exchange_rate)
        
        # Derive price tier
        price_tier = derive_price_tier(price_gbp)
        
        # Generate product ID
        product_id = generate_product_id(title, category, price_gbp)
        
        return {
            'product_id': product_id,
            'title': title,
            'price_gbp': price_gbp,
            'price_inr': price_inr,
            'category': category,
            'availability_status': status,
            'stock_quantity': quantity,
            'price_tier': price_tier
        }
        
    except Exception as e:
        logger.error(f"Error transforming product {product.get('title', 'Unknown')}: {e}")
        return None


def transform_products(products: List[Dict], exchange_rate: float) -> List[Dict]:
    """
    Transform a list of products
    
    Args:
        products: List of raw product dictionaries
        exchange_rate: GBP to INR exchange rate
        
    Returns:
        List of transformed product dictionaries
    """
    transformed = []
    
    for product in products:
        transformed_product = transform_product(product, exchange_rate)
        if transformed_product:
            transformed.append(transformed_product)
    
    logger.info(f"Transformed {len(transformed)} out of {len(products)} products")
    
    return transformed


if __name__ == "__main__":
    # Test transformation
    sample_product = {
        'title': '  A Light in the Attic  ',
        'price_gbp': 51.77,
        'category': 'poetry',
        'availability': 'In stock (22 available)'
    }
    
    exchange_rate = 105.50
    transformed = transform_product(sample_product, exchange_rate)
    print("Transformed product:", transformed)
