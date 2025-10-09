import sqlite3
import sys

DB = 'project_tracker.db'

def main():
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        if not tables:
            print('No tables found in', DB)
        else:
            print('Tables in', DB)
            for t in tables:
                print(' -', t[0])
        conn.close()
    except Exception as e:
        print('Error:', e)
        sys.exit(1)

if __name__ == '__main__':
    main()
import sqlite3
conn = sqlite3.connect('project_tracker.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())
conn.close()