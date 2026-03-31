import sqlite3

conn = sqlite3.connect("bus_pass.db")
cursor = conn.cursor()

cursor.execute("INSERT INTO routes VALUES (1, 'A', 'B', 10)")
cursor.execute("INSERT INTO buses VALUES (1, 'PMC-PCMC', 1, 'Driver1')")
cursor.execute("INSERT INTO pass_types VALUES (1, 'Daily', 1, 70)")

conn.commit()
conn.close()

print("Data inserted!")