import os
import psycopg2

from dotenv import load_dotenv
load_dotenv()

# Connect Database.
conn = psycopg2.connect(host = 'localhost', dbname = 'postgres', user = 'postgres', password = os.getenv('POSTGRES_DB_PASSWORD'), port = 5432)

# Create Cursor: To execute Queries(commands).
cur = conn.cursor()

cur.execute(
    """
        CREATE TABLE IF NOT EXISTS person(
            id INT PRIMARY KEY,
            name VARCHAR(255),
            age INT,
            gender CHAR
        );
    """
)

cur.execute(
    """
        INSERT INTO person (id, name, age, gender) VALUES 
        (1, 'Mohammed Sohail', 19, 'M'),
        (2, 'Muskan Anjum', 19, 'F'),
        (3, 'Mirza Ghalib', 23, 'M'),
        (4, 'Mohammed Saad', 21, 'M'),
        (5, 'Nayanika Sharma', 20, 'F')
    """
)

cur.execute(
    """
        SELECT * FROM person WHERE name = 'Muskan Anjum';
    """
)

print(cur.fetchone())

cur.execute(
    """
        SELECT * FROM person WHERE age <= 20;
    """    
)

print(cur.fetchall())

sql_query = cur.mogrify(""" SELECT * FROM person WHERE starts_with(name, %s) AND age < %s """, ('M', 20))

cur.execute(sql_query)
print(cur.fetchall())

conn.commit()

cur.close()
conn.close()