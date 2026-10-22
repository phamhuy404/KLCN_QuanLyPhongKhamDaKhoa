import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;')
cursor = conn.cursor()

try:
    cursor.execute("SELECT CAST('2026-10-22 19:40:51.363000' AS DATETIME)")
    print("DATETIME with 6 decimals:", cursor.fetchone())
except Exception as e:
    print("DATETIME with 6 decimals error:", e)

try:
    cursor.execute("SELECT CAST('2026-10-22 19:40:51.363' AS DATETIME)")
    print("DATETIME with 3 decimals:", cursor.fetchone())
except Exception as e:
    print("DATETIME with 3 decimals error:", e)

try:
    cursor.execute("SELECT CAST('2026-10-22 19:40:51.363000' AS DATETIME2)")
    print("DATETIME2:", cursor.fetchone())
except Exception as e:
    print("DATETIME2 error:", e)

conn.close()
