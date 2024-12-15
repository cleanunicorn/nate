from datetime import datetime
import sqlite3

class Storage:
    def __init__(self, db_path='storage.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the storage database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create table for key-value storage
        c.execute('''
            CREATE TABLE IF NOT EXISTS storage (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get(self, key, default=None):
        """Get a value from storage"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT value FROM storage WHERE key = ?', (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default

    def set(self, key, value):
        """Set a value in storage"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO storage (key, value, updated_at) 
            VALUES (?, ?, ?)
        ''', (key, str(value), datetime.now()))
        conn.commit()
        conn.close()

    def get_timestamp(self, key, default=None):
        """Get a timestamp value from storage"""
        value = self.get(key)
        if value:
            return datetime.fromisoformat(value)
        return default