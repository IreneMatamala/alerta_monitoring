import requests
import sqlite3
import time
import yaml
from datetime import datetime
from pathlib import Path

DB_PATH = "monitoring.db"
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "TSS-Monitor/1.0"
}

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status_code INTEGER,
            state TEXT,
            latency_ms INTEGER
        )
    """)
    conn.commit()
    conn.close()

def check_url(url, config):
    start_time = time.time()

    try:
        response = requests.get(
            url,
            timeout=config["timeout_seconds"],
            headers=HEADERS
        )
        latency = int((time.time() - start_time) * 1000)
        status = response.status_code

        if status == 200:
            state = "OK"
        elif status == 403:
            state = "BLOCKED"
        elif 400 <= status < 500:
            state = "CLIENT_ERROR"
        elif 500 <= status < 600:
            state = "SERVER_ERROR"
        else:
            state = "UNKNOWN"

    except requests.exceptions.Timeout:
        status = 0
        latency = 0
        state = "TIMEOUT"
    except requests.exceptions.RequestException:
        status = 0
        latency = 0
        state = "CONNECTION_ERROR"

    return status, state, latency

def save_check(url, status, state, latency):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO checks (url, timestamp, status_code, state, latency_ms)
        VALUES (?, ?, ?, ?, ?)
    """, (
        url,
        datetime.utcnow().isoformat(),
        status,
        state,
        latency
    ))
    conn.commit()
    conn.close()

def generate_daily_report():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            url,
            COUNT(*) AS total_checks,
            SUM(CASE WHEN state = 'OK' THEN 1 ELSE 0 END) AS ok_checks,
            AVG(latency_ms) AS avg_latency
        FROM checks
        GROUP BY url
    """)

    rows = cur.fetchall()
    conn.close()

    report_path = REPORTS_DIR / "daily_report.md"

    with open(report_path, "w") as report:
        report.write("# 📊 Informe Diario de Monitorización\n\n")
        report.write("| URL | Estado observado | Uptime (%) | Latencia media (ms) |\n")
        report.write("|-----|------------------|------------|--------------------|\n")

        for url, total, ok, avg_latency in rows:
            uptime = round((ok / total) * 100, 2) if total else 0
            avg_latency = int(avg_latency) if avg_latency else "N/A"

            estado = "OK" if uptime == 100 else "CON INCIDENTES"

            report.write(
                f"| {url} | {estado} | {uptime}% | {avg_latency} |\n"
            )

def main():
    config = load_config()
    init_db()

    for url in config["urls"]:
        status, state, latency = check_url(url, config)
        save_check(url, status, state, latency)

        if state == "OK":
            if latency > config["latency_critical_ms"]:
                print(f"[CRITICAL] {url} lenta ({latency} ms)")
            elif latency > config["latency_warning_ms"]:
                print(f"[WARNING] {url} lenta ({latency} ms)")
            else:
                print(f"[OK] {url} ({latency} ms)")
        else:
            print(f"[ALERTA] {url} → {state} (status {status})")

    generate_daily_report()

if __name__ == "__main__":
    main()
