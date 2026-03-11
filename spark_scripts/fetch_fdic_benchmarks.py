import requests
import csv
import os
from datetime import datetime
import psycopg2
import uuid

# Use relative path for local testing, Airflow will use absolute /opt/airflow/data
DATA_DIR = './data'
os.makedirs(DATA_DIR, exist_ok=True)

# Connection parameters
# Host is 'postgres' inside Docker, 'localhost' for local PowerShell runs
DB_PARAMS = {
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow",
    "host": "postgres" if os.getenv('AIRFLOW_HOME') else "localhost",
    "port": "5432"
}

def fetch_industry_benchmarks():
    print("Fetching data from FDIC BankFind API...")
    url = "https://banks.data.fdic.gov/api/financials"
    params = {
        "filters": "REPDTE:20231231 AND ASSET:[100000000 TO *]",
        "fields": "REPDTE,CERT,NAME,EQVWCOR", 
        "limit": 100,
        "format": "json"
    }

    response = requests.get(url, params=params)
    data = response.json().get('data', [])
    
    car_values = [float(item.get('data', {}).get('EQVWCOR')) 
                  for item in data if item.get('data', {}).get('EQVWCOR') is not None]
    
    avg_car = sum(car_values) / len(car_values) if car_values else 0.0
    
    # Prepare benchmarks list
    fetched_at = datetime.now()
    report_period = "20231231"
    benchmarks = [
        (report_period, 'CAR', round(avg_car, 2), fetched_at),
        (report_period, 'LCR', 100.00, fetched_at),
        (report_period, 'NPL', 1.50, fetched_at)
    ]

    # 1. Save to CSV (Audit Trail)
    output_file = os.path.join(DATA_DIR, 'fdic_benchmarks.csv')
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['report_period', 'metric_name', 'industry_average', 'fetched_at'])
        writer.writerows(benchmarks)
    print(f"Benchmarks saved to CSV: {output_file}")

    # 2. Push to PostgreSQL via psycopg2
    print(f"Connecting to PostgreSQL ({DB_PARAMS['host']}) to load benchmarks...")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Create table if it doesn't exist (Senior DE practice)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fdic_benchmarks (
                report_period VARCHAR(10),
                metric_name VARCHAR(10),
                industry_average NUMERIC,
                fetched_at TIMESTAMP
            );
        """)

        # Clear old benchmarks to keep it fresh
        cur.execute("DELETE FROM fdic_benchmarks;")

        insert_query = """
            INSERT INTO fdic_benchmarks (report_period, metric_name, industry_average, fetched_at)
            VALUES (%s, %s, %s, %s)
        """
        cur.executemany(insert_query, benchmarks)
        
        conn.commit()
        print("Successfully updated 'fdic_benchmarks' table in PostgreSQL.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    fetch_industry_benchmarks()