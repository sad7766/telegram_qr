import sqlite3

# Connect to the database
conn = sqlite3.connect('bot.db')

# Create a cursor
cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT * FROM user_history")

# Fetch and print the results
results = cursor.fetchall()
for row in results:
    print(row)

# Close the connection
conn.close()