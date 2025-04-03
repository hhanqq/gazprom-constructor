import psycopg2
# "postgresql://root:12345@db:5432/test_postg-db-1"
conn = psycopg2.connect(host="localhost", port="8888", database="postgres", user="postgres", password="mysecretpassword")
cur = conn.cursor()
cur.execute(query="SELECT * FROM users")

