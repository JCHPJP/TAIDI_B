"""
数据库工具模块 - 支持多线程查询和增删改
"""
import sqlite3
from pathlib import Path
from typing import List, Dict
import threading

class DatabaseHelper:
    """数据库操作工具类"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if not hasattr(self, 'initialized'):
            if db_path is None:
                db_path = Path(__file__).parent.parent / 'db' / 'financial_data.db'
            
            self.db_path = str(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 每个线程独立的连接
            self._local = threading.local()
            
            # 写操作锁（增删改需要串行执行）
            self._write_lock = threading.Lock()
            
            self.initialized = True
    
    def _get_connection(self):
        """获取当前线程的连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def query(self, sql: str) -> List[Dict]:
        """查询（多线程并发读，无需加锁）"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"查询错误: {e}")
            return []
    
    def execute(self, sql: str) -> int:
        """增删改（自动加锁，线程安全）"""
        with self._write_lock:  # 写操作串行化
            conn = self._get_connection()
            try:
                cursor = conn.execute(sql)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                print(f"执行错误: {e}")
                conn.rollback()
                return -1
    
    def executemany(self, sql: str, params_list: List[tuple]) -> int:
        """批量增删改（自动加锁，线程安全）"""
        with self._write_lock:
            conn = self._get_connection()
            try:
                conn.executemany(sql, params_list)
                conn.commit()
                return len(params_list)
            except Exception as e:
                print(f"批量执行错误: {e}")
                conn.rollback()
                return 0
    
    def close(self):
        """关闭当前线程的连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# 全局实例
db = DatabaseHelper()