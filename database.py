import sqlite3
from flask import g
import psycopg2
from psycopg2.extras import DictCursor

def connect_db():
    conn = psycopg2.connect('postgres://Subhayan:root123@159.65.148.192:5432/Subhayan',cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn,sql

def get_db():
    db = connect_db()
    if not hasattr(g,'postgres_db_con'):
        g.postgres_db_con = db[0]
    if not hasattr(g,'postgres_db_cur'):
        g.postgres_db_cur = db[1]
    return g.postgres_db_cur

def init_db():
    db = connect_db()
    db[1].execute(open('schema.sql','r').read())
    db[1].close()
    db[0].close()
    
