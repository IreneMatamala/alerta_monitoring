import requests
import sqlite3
import time
import yaml
from datetime import datetime

DB_NAME = "database.db"

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uptime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            url TEXT,
            status_code INTEGER,
            response_time REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def check_url(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start

        status = "UP" if response.status_code == 200 else "DOWN"

        return response.status_code, response_time, status

    except requests.exceptions.RequestException:
        return 0, 0, "DOWN"

def save_result(url, status_code, response_time, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO uptime (timestamp, url, status_code, response_time, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        url,
        status_code,
        response_time,
        status
    ))
    conn.commit()
    conn.close()

def generate_daily_report():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) as up_count,
               AVG(response_time) as avg_response
        FROM uptime
        GROUP BY url
    """)

    results = cursor.fetchall()
    conn.close()

    with open("reports/daily_report.md", "w") as report:
        report.write("# Informe diario de Uptime\n\n")
        report.write(f"Fecha: {datetime.utcnow().date()}\n\n")

        for url, total, up_count, avg_response in results:
            uptime_percent = (up_count / total) * 100 if total else 0
            report.write(f"## {url}\n")
            report.write(f"- Uptime: {uptime_percent:.2f}%\n")
            report.write(f"- Tiempo medio de respuesta: {avg_response:.2f} s\n\n")

def main():
    config = load_config()
    init_db()

    for url in config["urls"]:
        status_code, response_time, status = check_url(url)
        save_result(url, status_code, response_time, status)

        if status == "DOWN":
            print(f"[ALERTA] {url} no está disponible")

    generate_daily_report()

if __name__ == "__main__":
    main()
