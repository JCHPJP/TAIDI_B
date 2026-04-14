# database.py
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from config import DB_PATH

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_tables()
    def query(self, sql):
        return self.conn.execute(sql).fetchall()