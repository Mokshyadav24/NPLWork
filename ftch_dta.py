import mysql.connector
import pandas as pd
from datetime import datetime, date
import time
import os

# Function to calculate Modified Julian Date (MJD) with second precision
def datetime_to_mjd(dt):
    # MJD starts from 17 November 1858
    mjd_start = datetime(1858, 11, 17)
    delta_days = (dt - mjd_start).days + (dt - mjd_start).seconds / 86400
    return delta_days

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="ESP8266NPL",
    password="VCI_ioCJa1M574_p",
    database="arduino_data"
)
cursor = conn.cursor()

# Function to fetch data from the database
def fetch_data(date):
    query = "SELECT timestamp, X1, X2, Y1, Y2, D1, D2, Z1, Z2 FROM sensordata WHERE DATE(timestamp) = %s"
    cursor.execute(query, (date,))
    return cursor.fetchall()

# Function to get the last ID from the CSV
def get_last_id(file):
    if os.path.exists(file):
        df = pd.read_csv(file)
        return df['id'].max()
    return 0

# Initialize current_date and file names
current_date = date.today()
current_month = datetime.now().strftime("%B_%Y")
csv_file_daily = f'live_data_{current_date}.csv'
csv_file_monthly = f'month_{current_month}.csv'

# Continuous fetching loop
while True:
    # Check if the date has changed
    if date.today() != current_date:
        # Update the date and file names
        current_date = date.today()
        current_month = datetime.now().strftime("%B_%Y")
        csv_file_daily = f'live_data_{current_date}.csv'
        csv_file_monthly = f'month_{current_month}.csv'

    # Fetch data from the database
    records = fetch_data(current_date)
    if records:
        last_id_daily = get_last_id(csv_file_daily)  # Get the last used ID for daily file
        last_id_monthly = get_last_id(csv_file_monthly)  # Get the last used ID for monthly file
        
        # Create DataFrame
        df = pd.DataFrame(records, columns=['timestamp', 'X1', 'X2', 'Y1', 'Y2', 'D1', 'D2', 'Z1', 'Z2'])
        
        # Convert timestamp column to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate MJD for each entry with second precision
        df['mjd'] = df['timestamp'].apply(lambda dt: datetime_to_mjd(dt))

        # Assign unique IDs
        df['id'] = range(last_id_daily + 1, last_id_daily + len(df) + 1)
        df['unique_id'] = range(last_id_monthly + 1, last_id_monthly + len(df) + 1)

        # Save to daily CSV
        df.to_csv(csv_file_daily, mode='a', index=False, header=not os.path.exists(csv_file_daily))

        # Save to monthly CSV
        df.to_csv(csv_file_monthly, mode='a', index=False, header=not os.path.exists(csv_file_monthly))

        # Log the new entries
        print(f"Inserted data for {current_date}: {len(records)} new records")

        # Delete the records from the database after fetching
        delete_query = "DELETE FROM sensordata WHERE DATE(timestamp) = %s"
        cursor.execute(delete_query, (current_date,))
        conn.commit()

    # Sleep for 120 seconds before the next fetch
    time.sleep(240)

# Clean up
cursor.close()
conn.close()
