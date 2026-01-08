#!/usr/bin/env python3
"""
Database Viewer Utility
=======================

Inspect and view contents of the banking system database.
Shows all tables, relationships, and data in a readable format.
"""

import sys
import os
import sqlite3
from datetime import datetime
from typing import Optional

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import config
except ImportError:
    # If config not found, use defaults
    class config:
        DATABASE_PATH = "banking_system.db"


class DatabaseViewer:
    """View and inspect database contents"""
    
    def __init__(self, db_path: str = None):
        """Initialize viewer with database path"""
        self.db_path = db_path or config.DATABASE_PATH
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database file not found: {self.db_path}")
            print(f"💡 Run 'python chat.py' or 'python demo.py' first to create the database.")
            sys.exit(1)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def get_table_names(self):
        """Get all table names"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name: str):
        """Get table schema"""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def get_table_data(self, table_name: str, limit: int = 100):
        """Get data from table"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        return cursor.fetchall()
    
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_table(self, title: str, headers: list, rows: list, max_rows: int = 20):
        """Print data in table format"""
        if not rows:
            print(f"\n{title}: (empty)")
            return
        
        print(f"\n{title}: ({len(rows)} rows)")
        print("-" * 70)
        
        # Print headers
        print("  " + " | ".join(f"{h:^15}" for h in headers))
        print("  " + "-" * (len(headers) * 18))
        
        # Print rows (limited)
        for i, row in enumerate(rows[:max_rows]):
            values = []
            for val in row:
                if val is None:
                    values.append("NULL")
                elif isinstance(val, float):
                    values.append(f"{val:.2f}")
                elif isinstance(val, str) and len(val) > 15:
                    values.append(val[:12] + "...")
                else:
                    values.append(str(val))
            print("  " + " | ".join(f"{v:^15}" for v in values))
        
        if len(rows) > max_rows:
            print(f"  ... ({len(rows) - max_rows} more rows)")
    
    def view_overview(self):
        """Show database overview"""
        self.print_header("📊 DATABASE OVERVIEW")
        
        tables = self.get_table_names()
        
        print(f"\nDatabase: {self.db_path}")
        print(f"Tables: {len(tables)}")
        print("\nTable Counts:")
        
        total_rows = 0
        for table in tables:
            count = self.get_table_count(table)
            total_rows += count
            icon = "📋" if count > 0 else "⚪"
            print(f"  {icon} {table:.<30} {count:>5} rows")
        
        print(f"\nTotal Records: {total_rows}")
    
    def view_users(self):
        """Show users table"""
        self.print_header("👥 USERS")
        
        users = self.get_table_data('users')
        if not users:
            print("\n(No users in database)")
            return
        
        print(f"\nTotal Users: {len(users)}")
        print("-" * 70)
        
        for user in users:
            print(f"\n  User #{user['id']}: {user['username']}")
            print(f"    Balance: ${user['balance']:,.2f}")
            print(f"    Created: {user['created_at']}")
    
    def view_checks(self):
        """Show checks table"""
        self.print_header("📝 CHECKS")
        
        checks = self.get_table_data('checks', limit=50)
        if not checks:
            print("\n(No checks in database)")
            return
        
        # Get user names for reference
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username FROM users")
        users = {row['id']: row['username'] for row in cursor.fetchall()}
        
        # Group by status
        by_status = {}
        for check in checks:
            status = check['status']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(check)
        
        print(f"\nTotal Checks: {len(checks)}")
        
        for status in ['PENDING', 'ACCEPTED', 'DENIED', 'FORWARDED', 'TOKENIZED']:
            if status in by_status:
                print(f"\n{status} ({len(by_status[status])} checks):")
                print("-" * 70)
                
                for check in by_status[status][:10]:  # Limit to 10 per status
                    issuer = users.get(check['issuer_id'], 'Unknown')
                    payee = users.get(check['payee_id'], 'Unknown')
                    
                    print(f"  Check #{check['id']}: ${check['amount']:,.2f}")
                    print(f"    From: {issuer} → To: {payee}")
                    print(f"    Issued: {check['issued_at']}")
                    
                    if check['maturity_date']:
                        maturity = datetime.fromisoformat(check['maturity_date'])
                        print(f"    Maturity: {maturity.strftime('%Y-%m-%d %H:%M')}")
                
                if len(by_status[status]) > 10:
                    print(f"  ... ({len(by_status[status]) - 10} more)")
    
    def view_entities(self):
        """Show entities table"""
        self.print_header("🏢 ENTITIES (Counterparties)")
        
        entities = self.get_table_data('entities', limit=50)
        if not entities:
            print("\n(No entities in database)")
            return
        
        print(f"\nTotal Entities: {len(entities)}")
        print("-" * 70)
        
        # Sort by transaction count
        sorted_entities = sorted(entities, key=lambda e: e['total_transactions'], reverse=True)
        
        for entity in sorted_entities[:20]:  # Top 20
            print(f"\n  {entity['name']} ({entity['entity_type']})")
            print(f"    Transactions: {entity['total_transactions']}")
            print(f"    Volume: ${entity['total_volume']:,.2f}")
            print(f"    Reputation: {entity['reputation_score']:.1f}/100")
            print(f"    Last Interaction: {entity['last_interaction']}")
        
        if len(entities) > 20:
            print(f"\n  ... ({len(entities) - 20} more entities)")
    
    def view_transaction_history(self):
        """Show transaction history"""
        self.print_header("📜 TRANSACTION HISTORY")
        
        history = self.get_table_data('transaction_history', limit=50)
        if not history:
            print("\n(No transaction history)")
            return
        
        # Get users and entities for reference
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username FROM users")
        users = {row['id']: row['username'] for row in cursor.fetchall()}
        
        cursor.execute("SELECT id, name FROM entities")
        entities = {row['id']: row['name'] for row in cursor.fetchall()}
        
        print(f"\nTotal Transactions: {len(history)}")
        print("\nRecent Transactions:")
        print("-" * 70)
        
        for tx in history[:30]:  # Last 30
            user = users.get(tx['user_id'], 'Unknown')
            counterparty = entities.get(tx['counterparty_id'], 'N/A') if tx['counterparty_id'] else 'N/A'
            
            amount_str = f"${tx['amount']:,.2f}" if tx['amount'] else 'N/A'
            
            print(f"\n  [{tx['timestamp']}]")
            print(f"    User: {user}")
            print(f"    Operation: {tx['operation_type']}")
            print(f"    Counterparty: {counterparty}")
            print(f"    Amount: {amount_str}")
            print(f"    Status: {tx['status']}")
            print(f"    Confidence: {tx['intent_confidence']:.0%}" if tx['intent_confidence'] else "    Confidence: N/A")
            
            if tx['conversation_context'] and len(tx['conversation_context']) < 60:
                print(f"    Input: \"{tx['conversation_context']}\"")
        
        if len(history) > 30:
            print(f"\n  ... ({len(history) - 30} more transactions)")
    
    def view_tokens(self):
        """Show tokens table"""
        self.print_header("🪙 TOKENS (Layer 2)")
        
        tokens = self.get_table_data('tokens')
        if not tokens:
            print("\n(No tokens - Layer 2 not active)")
            return
        
        print(f"\nTotal Tokens: {len(tokens)}")
        print("-" * 70)
        
        for token in tokens:
            print(f"\n  Token #{token['id']}")
            print(f"    Check: #{token['check_id']}")
            print(f"    Owner: User #{token['owner_id']}")
            print(f"    Face Value: ${token['face_value']:,.2f}")
            print(f"    Discount: {token['discount_rate']:.1f}%")
            print(f"    Market Value: ${token['market_value']:,.2f}")
            print(f"    Status: {token['status']}")
            print(f"    Created: {token['created_at']}")
    
    def view_marketplace(self):
        """Show marketplace transactions"""
        self.print_header("🏪 MARKETPLACE TRANSACTIONS (Layer 2)")
        
        transactions = self.get_table_data('marketplace_transactions')
        if not transactions:
            print("\n(No marketplace transactions - Layer 2 not active)")
            return
        
        print(f"\nTotal Marketplace Transactions: {len(transactions)}")
        print("-" * 70)
        
        for tx in transactions:
            print(f"\n  Transaction #{tx['id']}")
            print(f"    Token: #{tx['token_id']}")
            print(f"    Seller: User #{tx['seller_id']}")
            print(f"    Buyer: User #{tx['buyer_id']}")
            print(f"    Price: ${tx['sale_price']:,.2f}")
            print(f"    Date: {tx['transaction_date']}")
    
    def view_statistics(self):
        """Show database statistics"""
        self.print_header("📈 STATISTICS")
        
        cursor = self.conn.cursor()
        
        # Check statistics
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM checks
            GROUP BY status
        """)
        check_stats = cursor.fetchall()
        
        if check_stats:
            print("\nCheck Statistics by Status:")
            print("-" * 70)
            for stat in check_stats:
                print(f"  {stat['status']:.<20} {stat['count']:>5} checks | "
                      f"Total: ${stat['total_amount']:>10,.2f} | "
                      f"Avg: ${stat['avg_amount']:>8,.2f}")
        
        # Operation statistics
        cursor.execute("""
            SELECT 
                operation_type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                AVG(intent_confidence) as avg_confidence
            FROM transaction_history
            GROUP BY operation_type
            ORDER BY count DESC
        """)
        op_stats = cursor.fetchall()
        
        if op_stats:
            print("\n\nOperation Statistics:")
            print("-" * 70)
            for stat in op_stats:
                success_rate = (stat['successful'] / stat['count'] * 100) if stat['count'] > 0 else 0
                conf = stat['avg_confidence'] or 0
                print(f"  {stat['operation_type']:.<20} {stat['count']:>5} ops | "
                      f"Success: {success_rate:>5.1f}% | "
                      f"Confidence: {conf:>5.1%}")
        
        # Entity statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_entities,
                AVG(total_transactions) as avg_transactions,
                AVG(total_volume) as avg_volume,
                AVG(reputation_score) as avg_reputation
            FROM entities
        """)
        entity_stat = cursor.fetchone()
        
        if entity_stat and entity_stat['total_entities'] > 0:
            print("\n\nEntity Statistics:")
            print("-" * 70)
            print(f"  Total Entities: {entity_stat['total_entities']}")
            print(f"  Avg Transactions per Entity: {entity_stat['avg_transactions']:.1f}")
            print(f"  Avg Volume per Entity: ${entity_stat['avg_volume']:,.2f}")
            print(f"  Avg Reputation Score: {entity_stat['avg_reputation']:.1f}/100")
    
    def view_all(self):
        """Show complete database dump"""
        self.print_header("🗄️  COMPLETE DATABASE VIEW")
        
        print(f"\nDatabase: {self.db_path}")
        print(f"Viewing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.view_overview()
        self.view_users()
        self.view_checks()
        self.view_entities()
        self.view_transaction_history()
        self.view_tokens()
        self.view_marketplace()
        self.view_statistics()
        
        print("\n" + "="*70)
        print("✅ Database view complete!")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='View banking system database contents')
    parser.add_argument('--db', type=str, help='Database file path (default: banking_system.db)')
    parser.add_argument('--overview', action='store_true', help='Show overview only')
    parser.add_argument('--users', action='store_true', help='Show users table')
    parser.add_argument('--checks', action='store_true', help='Show checks table')
    parser.add_argument('--entities', action='store_true', help='Show entities table')
    parser.add_argument('--history', action='store_true', help='Show transaction history')
    parser.add_argument('--tokens', action='store_true', help='Show tokens table')
    parser.add_argument('--marketplace', action='store_true', help='Show marketplace transactions')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    # Initialize viewer
    viewer = DatabaseViewer(args.db)
    
    try:
        # If no specific view requested, show all
        if not any([args.overview, args.users, args.checks, args.entities, 
                   args.history, args.tokens, args.marketplace, args.stats]):
            viewer.view_all()
        else:
            if args.overview:
                viewer.view_overview()
            if args.users:
                viewer.view_users()
            if args.checks:
                viewer.view_checks()
            if args.entities:
                viewer.view_entities()
            if args.history:
                viewer.view_transaction_history()
            if args.tokens:
                viewer.view_tokens()
            if args.marketplace:
                viewer.view_marketplace()
            if args.stats:
                viewer.view_statistics()
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
