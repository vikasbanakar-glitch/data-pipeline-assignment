# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Start the Pipeline
```bash
./start.sh
```

Or manually:
```bash
export AIRFLOW_UID=$(id -u)
docker-compose up -d
```

### Step 2: Access Airflow
- Open: http://localhost:8080
- Login: `admin` / `admin`

### Step 3: Run the DAG
1. Find `product_pricing_pipeline` in the DAG list
2. Toggle it **ON** (left side)
3. Click **▶ Trigger DAG** button

### Step 4: Monitor Progress
- Click on the DAG name
- View the Grid/Graph to see task progress
- Click on individual tasks to see logs

---

## 📊 Verify Results

### Check Products in Database
```bash
docker-compose exec postgres psql -U pipeline_user -d pipeline_db
```

Then run:
```sql
-- See how many products loaded
SELECT COUNT(*) FROM products;

-- View sample products
SELECT title, price_gbp, price_inr, category, price_tier 
FROM products 
LIMIT 10;

-- Check exchange rate
SELECT * FROM staging_exchange_rates;
```

---

## 🔍 Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Just Airflow scheduler
docker-compose logs -f airflow-scheduler

# Just PostgreSQL
docker-compose logs -f postgres
```

### Restart Services
```bash
docker-compose restart
```

### Stop Everything
```bash
docker-compose down
```

### Clean Restart (removes data)
```bash
docker-compose down -v
docker-compose up -d
```

---

## 🧪 Test Components

```bash
# Run all validation tests
docker-compose exec airflow-scheduler python /opt/airflow/test_pipeline.py

# Test scraper only
docker-compose exec airflow-scheduler python /opt/airflow/scripts/scrape_products.py

# Test exchange rate API
docker-compose exec airflow-scheduler python /opt/airflow/scripts/fetch_exchange_rate.py
```

---

## 🐛 Troubleshooting

### DAG not showing up?
```bash
# Check for parsing errors
docker-compose exec airflow-scheduler airflow dags list-import-errors

# List all DAGs
docker-compose exec airflow-scheduler airflow dags list
```

### Can't connect to database?
```bash
# Check PostgreSQL is running
docker-compose exec postgres pg_isready

# Verify tables exist
docker-compose exec postgres psql -U pipeline_user -d pipeline_db -c "\dt"
```

### Tasks failing?
- Check task logs in Airflow UI
- Review container logs: `docker-compose logs airflow-scheduler`
- Ensure internet connection (needed for scraping and API)

---

## 📈 Expected Results

After a successful run:
- **~100 products** scraped (5 pages × ~20 products)
- **1 exchange rate** stored
- **All products** transformed and loaded
- **Runtime**: 5-10 minutes

---

## 🎯 What the Pipeline Does

1. **Scrapes** book data from books.toscrape.com
2. **Fetches** GBP→INR exchange rate from API
3. **Transforms** data:
   - Cleans text fields
   - Normalizes categories
   - Converts prices to INR
   - Generates product IDs
   - Classifies price tiers
4. **Loads** everything into PostgreSQL

---

## 📞 Need Help?

Check the full [README.md](README.md) for:
- Detailed architecture
- Database schema
- Configuration options
- Advanced troubleshooting

---

**Pipeline Schedule**: Daily at midnight UTC  
**Default Pages**: 5 (configurable)  
**Load Strategy**: Full replace (configurable to upsert)
