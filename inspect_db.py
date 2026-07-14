import sqlite3

def inspect_db():
    conn = sqlite3.connect("data/db/nifty100.db")
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print("Tables in database:", tables)
    
    # Check rows count for each table
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"Table '{table}' has {count} rows")
        
        # Sample rows if they exist
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 2;")
            print(f"Sample from '{table}':", cursor.fetchall())
            
    conn.close()

if __name__ == '__main__':
    inspect_db()
