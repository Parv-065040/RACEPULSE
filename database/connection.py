"""
MySQL connection helper - Parv's ownership.
Reads connection details from environment variables, matching
docker-compose.yml / .env defaults.
"""
import os
import pymysql

def get_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "racepulse_user"),
        password=os.getenv("MYSQL_PASSWORD", "racepulse_pass"),
        database=os.getenv("MYSQL_DATABASE", "racepulse"),
        autocommit=True,
    )