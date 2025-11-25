import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    raise RuntimeError("SUPABASE_DB_URL not found in .env")

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)