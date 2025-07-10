import sqlite3

# Connect to sqlite
connection = sqlite3.connect("employee.db")

# Create a cursor object
cursor = connection.cursor()

# Drop table if already exists (for re-runs)
cursor.execute("DROP TABLE IF EXISTS EMPLOYEE")

# Create the EMPLOYEE table
table_info = """
CREATE TABLE EMPLOYEE (
    NAME VARCHAR(50),
    DEPARTMENT VARCHAR(50),
    SALARY INT
);
"""
cursor.execute(table_info)

# Sample 20 Indian employee records
employees = [
    ('Aarav', 'Engineering', 90000),
    ('Priya', 'Marketing', 60000),
    ('Raj', 'Finance', 72000),
    ('Anjali', 'HR', 58000),
    ('Vikram', 'Engineering', 85000),
    ('Sneha', 'Sales', 65000),
    ('Karan', 'Engineering', 78000),
    ('Meena', 'Finance', 70000),
    ('Ravi', 'Marketing', 62000),
    ('Pooja', 'Engineering', 88000),
    ('Alok', 'HR', 59000),
    ('Divya', 'Finance', 71000),
    ('Sameer', 'Sales', 63000),
    ('Neha', 'Engineering', 87000),
    ('Tanya', 'Marketing', 64000),
    ('Manish', 'Finance', 75000),
    ('Kavita', 'Sales', 66000),
    ('Rohit', 'HR', 60500),
    ('Lakshmi', 'Engineering', 89500),
    ('Amit', 'Sales', 67000)
]

# Insert records
cursor.executemany("INSERT INTO EMPLOYEE (NAME, DEPARTMENT, SALARY) VALUES (?, ?, ?)", employees)

# Commit and print the inserted records
connection.commit()

print("Inserted Records:")
for row in cursor.execute("SELECT * FROM EMPLOYEE"):
    print(row)

connection.close()
