import sqlite3
import json
import os
from datetime import datetime
import pandas as pd

# Use absolute path so the DB is always created/accessed inside the app/ folder
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments.db")

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Experiments table stores the pair of runs
    c.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            structure TEXT,
            trigger_type TEXT,
            turn_count INTEGER,
            patient_a TEXT,
            patient_b TEXT,
            t1_path TEXT,
            t2_path TEXT,
            pcr_score REAL,
            mean_spdi REAL,
            verdict TEXT,
            report_json TEXT
        )
    ''')
    
    # Migration: add 'structure' column if missing (for existing DBs)
    try:
        c.execute("ALTER TABLE experiments ADD COLUMN structure TEXT DEFAULT 'Unknown'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Migration: add 'swap_mode' column if missing
    try:
        c.execute("ALTER TABLE experiments ADD COLUMN swap_mode TEXT DEFAULT 'Position Swap'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

def add_experiment_result(trigger_type, turn_count, patient_a, patient_b,
                          t1_path, t2_path, report, structure="Unknown",
                          swap_mode="Position Swap"):
    """Save an experiment result (pair) to the DB."""
    conn = sqlite3.connect(DB_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract key metrics from report
    metrics = report.get("metrics", {})
    pcr = metrics.get("overall_pcr", 0.0)
    spdi = metrics.get("overall_spdi_magnitude", 0.0)
    verdict = metrics.get("verdict", "Unknown")

    sql = '''
        INSERT INTO experiments (
            timestamp, structure, trigger_type, turn_count, patient_a, patient_b,
            t1_path, t2_path, pcr_score, mean_spdi, verdict, report_json, swap_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    vals = (
        timestamp, structure, trigger_type, turn_count, patient_a, patient_b,
        t1_path, t2_path, pcr, spdi, verdict, json.dumps(report, ensure_ascii=False),
        swap_mode
    )
    
    conn.execute(sql, vals)
    conn.commit()
    conn.close()

def get_all_experiments():
    """Retrieve all experiments as a pandas DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query("SELECT * FROM experiments ORDER BY id DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_experiment_by_id(exp_id):
    """Retrieve a single experiment by ID."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def clear_all_experiments():
    """Delete all records from the experiments table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM experiments")
    conn.commit()
    conn.close()
