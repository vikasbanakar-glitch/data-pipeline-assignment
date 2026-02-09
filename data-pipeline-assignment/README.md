# Product Pricing Intelligence Pipeline

A daily ETL pipeline built with Apache Airflow that scrapes product data from books.toscrape.com, enriches it with currency exchange rates, and loads it into PostgreSQL for analytics.

## 🏗️ Architecture Overview

The pipeline consists of four main stages:

1. **Scraping**: Extract product data (title, price, category, availability) from books.toscrape.com
2. **Exchange Rate Fetching**: Retrieve GBP→INR exchange rates and store in staging table
3. **Transformation**: Clean, normalize, and enrich product data with currency conversion
4. **Loading**: Load transformed data into PostgreSQL products table

## 📋 Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- 4GB+ RAM available for containers
- Internet connection (for scraping and API calls)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd data-pipeline-assignment

# Create necessary directories
mkdir -p logs
```

### 2. Set Environment Variables (Optional)

The pipeline uses these default values, but you can override them:

```bash
export AIRFLOW_UID=$(id -u)
```

### 3. Start the Pipeline

```bash
# Start all services (Airflow + PostgreSQL)
docker-compose up -d

# Check services are running
docker-compose ps
```

This will:
- Initialize PostgreSQL with required schema
- Start Airflow webserver on port 8080
- Start Airflow scheduler

### 4. Access Airflow UI

1. Open browser to: http://localhost:8080
2. Login credentials:
   - **Username**: `admin`
   - **Password**: `admin`

### 5. Run the Pipeline

In the Airflow UI:
1. Find the DAG: `product_pricing_pipeline`
2. Toggle it **ON** (if paused)
3. Click "Trigger DAG" to run manually

The pipeline will:
- Scrape ~100 books (5 pages)
- Fetch current GBP→INR exchange rate
- Transform and load data
- Complete in 5-10 minutes

## 🗄️ Database Schema

### Tables

#### `staging_exchange_rates`
Stores daily exchange rate snapshots.

```sql
CREATE TABLE staging_exchange_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(10, 6) NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `products`
Final transformed product data.

```sql
CREATE TABLE products (
    product_id VARCHAR(64) PRIMARY KEY,
    title TEXT NOT NULL,
    price_gbp DECIMAL(10, 2) NOT NULL,
    price_inr DECIMAL(10, 2) NOT NULL,
    category VARCHAR(255),
    availability_status VARCHAR(50),
    stock_quantity INTEGER,
    price_tier VARCHAR(20),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `raw_products` (Optional)
Temporary storage for unprocessed data.

```sql
CREATE TABLE raw_products (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price_gbp DECIMAL(10, 2),
    category TEXT,
    availability TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Connect to Database

```bash
# Using docker-compose
docker-compose exec postgres psql -U pipeline_user -d pipeline_db

# Or from host (if port 5432 is exposed)
psql -h localhost -U pipeline_user -d pipeline_db
```

**Password**: `pipeline_pass`

### Query Examples

```sql
-- View all products
SELECT * FROM products LIMIT 10;

-- Check exchange rates
SELECT * FROM staging_exchange_rates ORDER BY date DESC;

-- Products by price tier
SELECT price_tier, COUNT(*), AVG(price_inr) as avg_price_inr
FROM products
GROUP BY price_tier;

-- Most expensive categories
SELECT category, AVG(price_gbp) as avg_price
FROM products
GROUP BY category
ORDER BY avg_price DESC
LIMIT 5;
```

## 🧪 Testing Individual Components

Each pipeline stage can be tested independently:

### Test Scraper

```bash
docker-compose exec airflow-scheduler python /opt/airflow/scripts/scrape_products.py
```

### Test Exchange Rate Fetcher

```bash
docker-compose exec airflow-scheduler python /opt/airflow/scripts/fetch_exchange_rate.py
```

### Test Data Transformation

```bash
docker-compose exec airflow-scheduler python /opt/airflow/scripts/transform_data.py
```

## 📁 Project Structure

```
data-pipeline-assignment/
├── dags/
│   └── product_pricing_dag.py       # Main Airflow DAG
├── scripts/
│   ├── scrape_products.py           # Web scraper
│   ├── fetch_exchange_rate.py       # Exchange rate API client
│   ├── transform_data.py            # Data transformations
│   └── load_data.py                 # Database loader
├── sql/
│   └── init.sql                     # Database initialization
├── config/                          # Configuration files (optional)
├── logs/                            # Airflow logs
├── docker-compose.yml               # Docker orchestration
├── Dockerfile                       # Custom Airflow image
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Configuration

### Database Connection

Set via environment variables in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_HOST: postgres
  POSTGRES_PORT: 5432
  POSTGRES_DB: pipeline_db
  POSTGRES_USER: pipeline_user
  POSTGRES_PASSWORD: pipeline_pass
```

### Scraping Settings

Modify in `scripts/scrape_products.py`:

```python
scrape_books(max_pages=5)  # Adjust number of pages
```

### DAG Schedule

Modify in `dags/product_pricing_dag.py`:

```python
schedule_interval='@daily'  # Change to '@hourly', '0 9 * * *', etc.
```

## 🛠️ Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready

# Check if tables exist
docker-compose exec postgres psql -U pipeline_user -d pipeline_db -c "\dt"
```

### DAG Not Appearing

1. Check DAG file syntax:
   ```bash
   docker-compose exec airflow-scheduler airflow dags list
   ```

2. View DAG parsing errors:
   ```bash
   docker-compose exec airflow-scheduler airflow dags list-import-errors
   ```

### Scraping Fails

- Verify internet connectivity in container
- Check if books.toscrape.com is accessible
- Review scraper logs in Airflow UI

## 🧹 Cleanup

### Stop Services

```bash
docker-compose down
```

### Remove All Data (including volumes)

```bash
docker-compose down -v
```

## 📊 Pipeline Features

### ✅ Implemented Features

- [x] Containerized with Docker Compose
- [x] Airflow DAG orchestration
- [x] Web scraping with BeautifulSoup
- [x] Exchange rate API integration
- [x] Data transformation and cleaning
- [x] PostgreSQL data loading
- [x] Idempotent operations (upsert support)
- [x] Retry logic on failures
- [x] Structured logging
- [x] Environment-based configuration
- [x] Parallel task execution (scraping + API)
- [x] XCom for inter-task communication

### 🎯 Data Transformations

1. **Text Cleaning**: Trim whitespace, normalize formatting
2. **Category Normalization**: Title case, handle unknowns
3. **Availability Parsing**: Extract status and stock quantity
4. **Currency Conversion**: GBP → INR with staging table lookup
5. **Price Tiering**: Classify as cheap/moderate/expensive
6. **Product ID Generation**: SHA256 hash for stable IDs

### 🔄 Idempotency

- Exchange rates use `ON CONFLICT` upsert
- Products table fully replaced each run (or upsert available)
- Same data yields same product IDs (deterministic hashing)

## 📈 Monitoring

### View Pipeline Runs

- Airflow UI: http://localhost:8080/dags/product_pricing_pipeline/grid
- Check task logs for detailed execution info
- Monitor task duration and success rates

### Database Metrics

```sql
-- Total products loaded
SELECT COUNT(*) FROM products;

-- Latest scrape timestamp
SELECT MAX(scraped_at) FROM products;

-- Exchange rate history
SELECT date, exchange_rate FROM staging_exchange_rates ORDER BY date DESC;
```

## 🤝 Contributing

To enhance this pipeline:

1. Add data quality checks (Great Expectations)
2. Implement data lineage tracking
3. Add alerting (Slack, email)
4. Create data visualization dashboard
5. Add unit tests for transformation logic
6. Implement incremental loading strategy

## 📝 License

This project is created for educational purposes.

## 🙋 Support

For issues or questions:
1. Check Airflow logs in UI
2. Review container logs: `docker-compose logs -f`
3. Verify database connectivity
4. Ensure all dependencies are installed

---

**Built with**: Apache Airflow, PostgreSQL, Python, Docker, BeautifulSoup

**Pipeline Schedule**: Daily at midnight UTC

**Data Retention**: Replace on each run (configurable for upsert)
