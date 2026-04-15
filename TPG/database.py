import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'vacuum_data.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vacuum_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            pressure REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(pressure, status="OK"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO vacuum_logs (timestamp, pressure, status) VALUES (?, ?, ?)', (timestamp, pressure, status))
    conn.commit()
    conn.close()

def get_latest_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT timestamp, pressure FROM vacuum_logs ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return {"timestamp": row[0], "pressure": row[1]}
    return {"timestamp": "N/A", "pressure": 0.0}

def get_history_data(start_str, end_str):
    # start_str, end_str format: 'YYYY-MM-DD HH:MM:SS'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT timestamp, pressure FROM vacuum_logs 
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
    ''', (start_str, end_str))
    rows = c.fetchall()
    conn.close()
    
    return [{"timestamp": row[0], "pressure": row[1]} for row in rows]
