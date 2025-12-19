import psutil
from datetime import datetime
import pymysql

# Connect to MySQL database
db = pymysql.connect(host='localhost', user='root', password='password', db='ganuda_view')
cursor = db.cursor()

# Define the heartbeat agent function
def ganuda_view_heartbeat():
    # Collect CPU, memory, disk, and load average metrics
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    load_avg = os.getloadavg()[0]

    # Insert metrics into MySQL database
    cursor.execute("INSERT INTO ganuda_view_heartbeats (cpu_percent, memory_percent, disk_percent, load_avg) VALUES (%s, %s, %s, %s)", (cpu_percent, memory_percent, disk_percent, load_avg))
    db.commit()

# Set up cron job to run the heartbeat agent every 5 minutes
cron = CronTab(user='root')
cron.minute.every(5).do(ganuda_view_heartbeat)