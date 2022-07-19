from django.test import TestCase

# Create your tests here.
import sqlite3
conn = sqlite3.connect('../db.sqlite3')
cursor = conn.cursor()
#cursor.execute('DELETE FROM my_info')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
result = cursor.fetchone()
print(result)
# # con.commit()
# cursor.execute('SELECT JSON(\'{"a": "b"}\')')