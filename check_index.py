import psycopg2

conn = psycopg2.connect('postgresql://pmuser:password@localhost:5432/proj_mgmt_db')
cur = conn.cursor()
cur.execute("SELECT relname, relkind FROM pg_class WHERE relname = 'idx_roles_deleted_at';")
print("pg_class:", cur.fetchall())

cur.execute("SELECT relname, relkind FROM pg_class WHERE relname LIKE 'idx_roles%';")
print("pg_class like idx_roles:", cur.fetchall())

conn.close()
