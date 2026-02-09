"""
Web scraper for books.toscrape.com
Extracts product title, price (GBP), category, and availability
"""
import logging
import re
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_books(base_url: str = "https://books.toscrape.com", max_pages: int = 5) -> List[Dict]:
    """
    Scrape product data from books.toscrape.com
    
    Args:
        base_url: Base URL of the website
        max_pages: Maximum number of pages to scrape
        
    Returns:
        List of dictionaries containing product data
    """
    products = []
    
    for page_num in range(1, max_pages + 1):
        try:
            # Construct page URL
            if page_num == 1:
                url = f"{base_url}/catalogue/page-{page_num}.html"
            else:
                url = f"{base_url}/catalogue/page-{page_num}.html"
            
            logger.info(f"Scraping page {page_num}: {url}")
            
            # Fetch page content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all product containers
            product_containers = soup.find_all('article', class_='product_pod')
            
            if not product_containers:
                logger.warning(f"No products found on page {page_num}")
                break
            
            for product in product_containers:
                try:
                    # Extract title
                    title_element = product.find('h3').find('a')
                    title = title_element.get('title', '').strip()
                    
                    # Extract price (remove £ symbol)
                    price_element = product.find('p', class_='price_color')
                    price_text = price_element.text.strip()
                    price_gbp = float(re.sub(r'[^\d.]', '', price_text))
                    
                    # Extract availability
                    availability_element = product.find('p', class_='instock availability')
                    availability = availability_element.text.strip() if availability_element else 'Unknown'
                    
                    # Get product detail URL to fetch category
                    product_url = product.find('h3').find('a')['href']
                    full_product_url = f"{base_url}/catalogue/{product_url.replace('../', '')}"
                    
                    # Fetch product detail page for category
                    category = fetch_product_category(full_product_url)
                    
                    products.append({
                        'title': title,
                        'price_gbp': price_gbp,
                        'category': category,
                        'availability': availability
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting product data: {e}")
                    continue
            
            logger.info(f"Scraped {len(product_containers)} products from page {page_num}")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page_num}: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error on page {page_num}: {e}")
            break
    
    logger.info(f"Total products scraped: {len(products)}")
    return products


def fetch_product_category(product_url: str) -> str:
    """
    Fetch the category of a product from its detail page
    
    Args:
        product_url: Full URL to the product detail page
        
    Returns:
        Category name or 'Unknown'
    """
    try:
        response = requests.get(product_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Category is in breadcrumb
        breadcrumb = soup.find('ul', class_='breadcrumb')
        if breadcrumb:
            category_links = breadcrumb.find_all('a')
            if len(category_links) >= 3:
                return category_links[2].text.strip()
        
        return 'Unknown'
        
    except Exception as e:
        logger.warning(f"Could not fetch category from {product_url}: {e}")
        return 'Unknown'


if __name__ == "__main__":
    # Test the scraper
    books = scrape_books(max_pages=2)
    print(f"Scraped {len(books)} books")
    if books:
        print("Sample product:", books[0])
