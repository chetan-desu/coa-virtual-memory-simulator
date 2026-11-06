"""
storage.py
==========
Handles all data persistence for the Virtual Memory Simulator.

Features:
  1. SQLite database to store simulation history (runs persist across sessions).
  2. Functions to save and retrieve simulation results.
  3. CSV export of simulation history.

CONCEPT (for beginners):
  SQLite is a lightweight database stored as a single file.
  Python includes it built-in (no installation needed).
  We use it so users can review past simulation runs.
"""

import sqlite3
import json
import io
import os
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# Database path — stored next to app.py in project root
# ---------------------------------------------------------------------------
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_CURRENT_DIR) == "simulator":
    _DB_DIR = os.path.dirname(_CURRENT_DIR)
else:
    _DB_DIR = _CURRENT_DIR
DB_PATH = os.path.join(_DB_DIR, "simulation_history.db")


# ---------------------------------------------------------------------------
# Initialize the database
# ---------------------------------------------------------------------------
def init_db() -> None:
    """
    Create the SQLite database and tables if they don't exist yet.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.

    Table: simulations
      id           INTEGER PRIMARY KEY AUTOINCREMENT
      timestamp    TEXT    — when the simulation was run
      algorithm    TEXT    — FIFO / LRU / Optimal / LFU
      pages        TEXT    — JSON-encoded reference string
      num_frames   INTEGER — number of frames used
      hits         INTEGER — total hits
      faults       INTEGER — total faults
      hit_ratio    REAL    — hit ratio (0–1)
      fault_ratio  REAL    — fault ratio (0–1)
      exec_time_ms REAL    — execution time in ms
      steps        TEXT    — JSON-encoded step-by-step trace
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT    NOT NULL,
            algorithm    TEXT    NOT NULL,
            pages        TEXT    NOT NULL,
            num_frames   INTEGER NOT NULL,
            hits         INTEGER NOT NULL,
            faults       INTEGER NOT NULL,
            hit_ratio    REAL    NOT NULL,
            fault_ratio  REAL    NOT NULL,
            exec_time_ms REAL    NOT NULL,
            steps        TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Save a simulation result
# ---------------------------------------------------------------------------
def save_simulation(result: dict, pages: list) -> int:
    """
    Save one simulation result to the database.

    Parameters
    ----------
    result : dict  — output from any run_* function in page_replacement.py
    pages  : list  — the original reference string

    Returns
    -------
    int — the auto-generated ID of the saved row
    """
    init_db()
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO simulations
            (timestamp, algorithm, pages, num_frames,
             hits, faults, hit_ratio, fault_ratio, exec_time_ms, steps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        result["algorithm"],
        json.dumps(pages),
        len(result["steps"][0]["frames"]) if result["steps"] else 0,
        result["hits"],
        result["faults"],
        result["hit_ratio"],
        result["fault_ratio"],
        result["execution_time_ms"],
        json.dumps(result["steps"]),
    ))

    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def save_all_results(results: list[dict], pages: list) -> None:
    """Save all 4 algorithm results (from compare_all) in one call."""
    for result in results:
        save_simulation(result, pages)


# ---------------------------------------------------------------------------
# Retrieve history
# ---------------------------------------------------------------------------
def get_history() -> pd.DataFrame:
    """
    Retrieve all simulation runs from the database.

    Returns
    -------
    pandas DataFrame with columns:
      ID, Timestamp, Algorithm, Pages, Frames, Hits, Faults,
      Hit Ratio, Fault Ratio, Exec Time (ms)
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT
            id           AS "ID",
            timestamp    AS "Timestamp",
            algorithm    AS "Algorithm",
            pages        AS "Pages (JSON)",
            num_frames   AS "Frames",
            hits         AS "Hits",
            faults       AS "Faults",
            hit_ratio    AS "Hit Ratio",
            fault_ratio  AS "Fault Ratio",
            exec_time_ms AS "Exec Time (ms)"
        FROM simulations
        ORDER BY id DESC
    """, conn)
    conn.close()

    # Decode JSON page strings for readability
    df["Reference String"] = df["Pages (JSON)"].apply(
        lambda x: ", ".join(map(str, json.loads(x)))
    )
    df = df.drop(columns=["Pages (JSON)"])

    return df


def get_simulation_steps(sim_id: int) -> list[dict]:
    """
    Retrieve the step-by-step trace for a specific simulation run.

    Parameters
    ----------
    sim_id : int — the simulation ID from the database

    Returns
    -------
    list of step dicts
    """
    init_db()
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT steps FROM simulations WHERE id = ?", (sim_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return []


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------
def export_csv(df: pd.DataFrame) -> bytes:
    """
    Convert a DataFrame to CSV bytes for Streamlit download button.

    Parameters
    ----------
    df : pandas DataFrame

    Returns
    -------
    bytes — UTF-8 encoded CSV
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Clear history
# ---------------------------------------------------------------------------
def clear_history() -> None:
    """Delete all records from the simulations table."""
    init_db()
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM simulations")
    conn.commit()
    conn.close()


def get_summary_stats() -> dict:
    """
    Return summary statistics across all saved simulations.
    Used by the History page dashboard cards.
    """
    init_db()
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM simulations")
    total_runs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT algorithm, AVG(hit_ratio), AVG(fault_ratio), COUNT(*)
        FROM simulations
        GROUP BY algorithm
    """)
    rows = cursor.fetchall()
    conn.close()

    algo_stats = {}
    for row in rows:
        algo_stats[row[0]] = {
            'avg_hit_ratio':   round(row[1], 4),
            'avg_fault_ratio': round(row[2], 4),
            'run_count':       row[3],
        }

    return {
        'total_runs': total_runs,
        'by_algorithm': algo_stats,
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing storage module...")
    init_db()
    print(f"Database created at: {DB_PATH}")

    # Simulate saving a dummy result
    dummy_result = {
        "algorithm":        "FIFO",
        "steps":            [{"step": 1, "page": 1, "frames": [1, -1, -1],
                              "fault": True, "hit": False, "replaced": None}],
        "hits":             3,
        "faults":           7,
        "hit_ratio":        0.3,
        "fault_ratio":      0.7,
        "execution_time_ms": 0.12,
    }
    row_id = save_simulation(dummy_result, [1, 2, 3, 1, 4, 1, 2])
    print(f"Saved simulation with ID: {row_id}")

    df = get_history()
    print(f"History has {len(df)} row(s).")
    print(df.to_string())
