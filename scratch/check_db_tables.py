import pyodbc

conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=quan_ly_phong_kham;Trusted_Connection=yes;')
c = conn.cursor()
c.execute("""
    SELECT t.name, SUM(p.rows) 
    FROM sys.tables t 
    JOIN sys.partitions p ON t.object_id = p.object_id 
    WHERE p.index_id IN (0,1) 
    GROUP BY t.name 
    ORDER BY t.name
""")
for r in c.fetchall():
    print(f"{r[0]}: {r[1]}")
conn.close()
