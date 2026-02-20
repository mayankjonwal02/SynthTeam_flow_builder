import mysql.connector
import psycopg2


# ================= MYSQL ================= #
def setup_mysql():
    print("🔵 Setting up MySQL...")

    # Connect to MySQL server (not DB yet)
    mysql_conn = mysql.connector.connect(
        host="localhost",
        port=13306,
        user="appuser",
        password="apppass"
    )
    cursor = mysql_conn.cursor()

    # Create DB
    cursor.execute("CREATE DATABASE IF NOT EXISTS dummytat;")
    cursor.execute("USE dummytat;")

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            city VARCHAR(100) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            school_id INT,
            FOREIGN KEY (school_id) REFERENCES school(id)
        );
    """)

    # Insert dummy data
    schools = [
        ("Green Valley School", "Delhi"),
        ("Sunrise Public School", "Mumbai"),
        ("Hill View Academy", "Bangalore")
    ]

    students = [
        ("Aman", 14, 1),
        ("Riya", 15, 1),
        ("Karan", 13, 2),
        ("Neha", 14, 3),
        ("Arjun", 16, 2)
    ]

    cursor.executemany(
        "INSERT INTO school (name, city) VALUES (%s, %s);",
        schools
    )

    cursor.executemany(
        "INSERT INTO student (name, age, school_id) VALUES (%s, %s, %s);",
        students
    )

    mysql_conn.commit()
    cursor.close()
    mysql_conn.close()

    print("✅ MySQL ready")


# ================= POSTGRES ================= #
def setup_postgres():
    print("🟢 Setting up PostgreSQL...")

    pg_conn = psycopg2.connect(
        host="localhost",
        port=15432,
        user="appuser",
        password="apppass",
        dbname="dummytat"
    )
    cursor = pg_conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            city VARCHAR(100) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT NOT NULL,
            school_id INT REFERENCES school(id)
        );
    """)

    # Insert dummy data
    schools = [
        ("Green Valley School", "Delhi"),
        ("Sunrise Public School", "Mumbai"),
        ("Hill View Academy", "Bangalore")
    ]

    students = [
        ("Aman", 14, 1),
        ("Riya", 15, 1),
        ("Karan", 13, 2),
        ("Neha", 14, 3),
        ("Arjun", 16, 2)
    ]

    for s in schools:
        cursor.execute(
            "INSERT INTO school (name, city) VALUES (%s, %s);", s
        )

    for s in students:
        cursor.execute(
            "INSERT INTO student (name, age, school_id) VALUES (%s, %s, %s);", s
        )

    pg_conn.commit()
    cursor.close()
    pg_conn.close()

    print("✅ PostgreSQL ready")


# ================= RUN ================= #
if __name__ == "__main__":
    setup_mysql()
    setup_postgres()
    print("\n🎯 All databases, tables, and data created successfully")