"""
Database Schema - Updated for Persistent Check IDs
==================================================
"""
import sqlite3
import json
from datetime import datetime, date

class DatabaseManager:
    def __init__(self, db_path: str = "banking_system.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn: self.conn.close()
    
    def initialize_schema(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ADDED: sender_id to track who forwarded the check
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issuer_id INTEGER NOT NULL,
                payee_id INTEGER NOT NULL,
                sender_id INTEGER, 
                amount REAL NOT NULL,
                status TEXT DEFAULT 'PENDING',
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                maturity_date TIMESTAMP,
                parent_check_id INTEGER,
                FOREIGN KEY (issuer_id) REFERENCES users(id),
                FOREIGN KEY (payee_id) REFERENCES users(id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                CHECK (status IN ('PENDING', 'ACCEPTED', 'DENIED', 'FORWARDED', 'TOKENIZED'))
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                entity_type TEXT DEFAULT 'USER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_transactions INTEGER DEFAULT 0,
                total_volume REAL DEFAULT 0.0,
                reputation_score REAL DEFAULT 50.0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                operation_type TEXT NOT NULL,
                counterparty_id INTEGER,
                check_id INTEGER,
                token_id INTEGER,
                amount REAL,
                status TEXT NOT NULL,
                conversation_context TEXT,
                intent_confidence REAL,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

class EntityManager:
    def __init__(self, db_manager): self.db = db_manager
    
    def get_or_create_entity(self, name: str, entity_type: str = 'USER') -> int:
        cursor = self.db.conn.cursor()
        # Case insensitive check
        cursor.execute("SELECT id FROM entities WHERE LOWER(name) = LOWER(?)", (name.strip(),))
        if res := cursor.fetchone(): return res[0]
        try:
            cursor.execute("INSERT INTO entities (name, entity_type) VALUES (?, ?)", (name.strip(), entity_type))
            self.db.conn.commit()
            return cursor.lastrowid
        except: return 0 # Handle race condition

class TransactionLogger:
    def __init__(self, db_manager): self.db = db_manager
    
    def log_transaction(self, user_id, operation_type, status, **kwargs):
        cursor = self.db.conn.cursor()
        def json_serial(obj): return obj.isoformat() if isinstance(obj, (datetime, date)) else str(obj)
        meta = json.dumps(kwargs.get('metadata'), default=json_serial) if kwargs.get('metadata') else None
        
        try:
            cursor.execute("""
                INSERT INTO transaction_history (
                    user_id, operation_type, counterparty_id, check_id, 
                    token_id, amount, status, conversation_context, 
                    intent_confidence, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, operation_type, kwargs.get('counterparty_id'),
                kwargs.get('check_id'), kwargs.get('token_id'), kwargs.get('amount'), 
                status, kwargs.get('conversation_context'), kwargs.get('intent_confidence'), meta
            ))
            self.db.conn.commit()
        except: pass
    
    def get_user_history(self, user_id, limit=50):
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM transaction_history WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        return [dict(r) for r in c.fetchall()]