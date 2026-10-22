import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;')
c = conn.cursor()
c.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'don_thuoc'")
for r in c.fetchall():
    print(f"{r[0]}: {r[1]}")
conn.close()
