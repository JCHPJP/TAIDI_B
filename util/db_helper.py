"""
数据库工具模块
项目中所有文件都可以导入使用
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

class DatabaseHelper:
    """数据库操作工具类"""
    
    _instance = None  # 单例模式
    
    def __new__(cls, db_path: str = None):
        """单例模式，确保全局只有一个数据库连接"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        if not hasattr(self, 'initialized'):
            if db_path is None:
                db_path = Path(__file__).parent.parent / 'db' / 'financial_data.db'
            
            self.db_path = str(db_path)
            self.conn = None
            
            # 确保数据库目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.initialized = True
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def query(self, sql: str, params: dict = None) -> List[Dict]:
        """执行查询"""
        try:
            if params:
                cursor = self.conn.execute(sql, params)
            else:
                cursor = self.conn.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"查询错误: {e}")
            return []
    
    def execute(self, sql: str, params: dict = None) -> int:
        """执行增删改"""
        try:
            if params:
                cursor = self.conn.execute(sql, params)
            else:
                cursor = self.conn.execute(sql)
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"执行错误: {e}")
            self.conn.rollback()
            return -1
    
    def executemany(self, sql: str, params_list: List[dict]) -> int:
        """批量执行"""
        try:
            self.conn.executemany(sql, params_list)
            self.conn.commit()
            return len(params_list)
        except Exception as e:
            print(f"批量执行错误: {e}")
            self.conn.rollback()
            return 0


# 创建全局实例（方便直接导入使用）
db = DatabaseHelper()
if __name__ == "__main__":
    # 测试连接和查询
    db.connect()
    # result = db.query("SELECT * FROM sqlite_master WHERE type='table';")
    # print("数据库中的表:", result)
    db.close()
    print(Path(__file__))