"""
Initializes SQLite database from mock_data.json.
Stores profiles, PTO balances, and benefits elections in relational tables.
Satisfies Requirement 7.
"""

import json
import sqlite3
from pathlib import Path

def init_database():
    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / "data" / "mock_db" / "mock_data.json"
    sqlite_path = base_dir / "data" / "mock_db" / "hr_mock.db"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        manager TEXT,
        office_location TEXT NOT NULL,
        employment_type TEXT NOT NULL CHECK(employment_type IN ('full-time', 'part-time', 'contractor')),
        hire_date TEXT NOT NULL,
        tenure_months INTEGER NOT NULL,
        FOREIGN KEY (manager) REFERENCES employees(employee_id)
    );
    """)
    
    # 2. PTO Balances table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pto_balances (
        employee_id TEXT PRIMARY KEY,
        accrued_days INTEGER NOT NULL CHECK(accrued_days >= 0 AND accrued_days <= 60),
        used_days INTEGER NOT NULL CHECK(used_days >= 0 AND used_days <= 60),
        remaining_days INTEGER NOT NULL CHECK(remaining_days >= 0 AND remaining_days <= 60),
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)
    
    # 3. Benefits Elections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benefits_elections (
        employee_id TEXT PRIMARY KEY,
        health_plan TEXT NOT NULL CHECK(health_plan IN ('enrolled', 'waived')),
        dental TEXT NOT NULL CHECK(dental IN ('enrolled', 'waived')),
        vision TEXT NOT NULL CHECK(vision IN ('enrolled', 'waived')),
        retirement_contribution TEXT NOT NULL CHECK(retirement_contribution IN ('enrolled', 'waived')),
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)
    
    # Clear existing rows
    cursor.execute("DELETE FROM benefits_elections;")
    cursor.execute("DELETE FROM pto_balances;")
    cursor.execute("DELETE FROM employees;")
    
    for emp in data["employees"]:
        cursor.execute("""
        INSERT INTO employees (
            employee_id, name, department, role, manager,
            office_location, employment_type, hire_date, tenure_months
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            emp["employee_id"], emp["name"], emp["department"], emp["role"],
            emp["manager"], emp["office_location"], emp["employment_type"],
            emp["hire_date"], emp["tenure_months"]
        ))
        
        pto = emp["pto_balance"]
        cursor.execute("""
        INSERT INTO pto_balances (employee_id, accrued_days, used_days, remaining_days)
        VALUES (?, ?, ?, ?);
        """, (
            emp["employee_id"], pto["accrued_days"], pto["used_days"], pto["remaining_days"]
        ))
        
        ben = emp["benefits"]
        cursor.execute("""
        INSERT INTO benefits_elections (employee_id, health_plan, dental, vision, retirement_contribution)
        VALUES (?, ?, ?, ?, ?);
        """, (
            emp["employee_id"], ben["health_plan"], ben["dental"], ben["vision"], ben["retirement_contribution"]
        ))
        
    conn.commit()
    conn.close()
    print(f"Successfully initialized SQLite database at {sqlite_path} with {len(data['employees'])} employees.")

if __name__ == "__main__":
    init_database()
