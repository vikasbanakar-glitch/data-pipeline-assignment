-- Create pipeline database and user
CREATE DATABASE pipeline_db;
CREATE USER pipeline_user WITH PASSWORD 'pipeline_pass';
GRANT ALL PRIVILEGES ON DATABASE pipeline_db TO pipeline_user;

-- Connect to pipeline_db
\c pipeline_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO pipeline_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO pipeline_user;

-- Create staging table for exchange rates
CREATE TABLE IF NOT EXISTS staging_exchange_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    base_currency VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    exchange_rate DECIMAL(10, 6) NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rate_per_day UNIQUE (date, base_currency, target_currency)
);

-- Create optional raw products table
CREATE TABLE IF NOT EXISTS raw_products (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price_gbp DECIMAL(10, 2),
    category TEXT,
    availability TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create final products table
CREATE TABLE IF NOT EXISTS products (
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

-- Create indexes for better query performance
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price_tier ON products(price_tier);
CREATE INDEX idx_staging_exchange_rates_date ON staging_exchange_rates(date);

-- Grant permissions to pipeline user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pipeline_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pipeline_user;
