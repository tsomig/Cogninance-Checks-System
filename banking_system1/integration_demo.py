"""
Integration Demo: IntentParser + Database + Entity Management
============================================================

This script demonstrates how all components work together in a
complete workflow from natural language input to database logging.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser


class ConversationalBankingDemo:
    """
    Demonstration of the conversational banking system.
    Shows integration between IntentParser, EntityManager, and TransactionLogger.
    """
    
    def __init__(self, db_path="demo_banking.db"):
        # Initialize components
        self.db = DatabaseManager(db_path)
        self.db.connect()
        self.db.initialize_schema()
        
        self.parser = IntentParser()
        self.entity_mgr = EntityManager(self.db)
        self.logger = TransactionLogger(self.db)
        
        # Create a demo user
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, username, balance) 
            VALUES (1, 'demo_user', 5000.0)
        """)
        self.db.conn.commit()
        self.user_id = 1
    
    def process_command(self, user_input: str):
        """
        Process a single user command through the entire pipeline.
        """
        print(f"\n{'='*60}")
        print(f"USER: {user_input}")
        print(f"{'='*60}")
        
        # Step 1: Parse intent
        intent = self.parser.parse(user_input)
        print(f"\n🧠 INTENT PARSER:")
        print(f"  Operation: {intent.operation}")
        print(f"  Confidence: {intent.confidence:.0%}")
        print(f"  Parameters: {intent.parameters}")
        
        # Step 2: Check if we need clarification
        if intent.needs_clarification():
            print(f"\n⚠️  NEEDS CLARIFICATION:")
            for ambiguity in intent.ambiguities:
                print(f"  - {ambiguity}")
            return
        
        # Step 3: Resolve entities
        counterparty_id = None
        if 'counterparty' in intent.parameters:
            counterparty_name = intent.parameters['counterparty']
            counterparty_id = self.entity_mgr.get_or_create_entity(
                counterparty_name, 
                'USER'
            )
            print(f"\n🏢 ENTITY RESOLVED:")
            print(f"  {counterparty_name.title()} → ID {counterparty_id}")
        
        # Step 4: Execute operation (simulated)
        print(f"\n⚙️  EXECUTING OPERATION:")
        print(f"  {intent.operation} initiated...")
        
        # Simulate success
        status = 'SUCCESS'
        
        # Step 5: Log transaction
        tx_id = self.logger.log_transaction(
            user_id=self.user_id,
            operation_type=intent.operation,
            status=status,
            counterparty_id=counterparty_id,
            amount=intent.parameters.get('amount'),
            check_id=intent.parameters.get('check_id'),
            token_id=intent.parameters.get('token_id'),
            conversation_context=user_input,
            intent_confidence=intent.confidence,
            metadata={'simulated': True}
        )
        
        print(f"  ✓ Operation completed")
        print(f"\n📝 TRANSACTION LOGGED:")
        print(f"  Transaction ID: {tx_id}")
        print(f"  Status: {status}")
        
        # Step 6: Update entity stats if applicable
        if counterparty_id and 'amount' in intent.parameters:
            self.entity_mgr.update_entity_stats(
                counterparty_id, 
                intent.parameters['amount']
            )
            print(f"\n📊 ENTITY STATS UPDATED")
    
    def show_summary(self):
        """Show summary of all activity"""
        print(f"\n\n{'='*60}")
        print("SYSTEM SUMMARY")
        print(f"{'='*60}")
        
        # Show entities
        entities = self.entity_mgr.list_entities()
        print(f"\n🏢 ENTITIES ({len(entities)} total):")
        for entity in entities:
            print(f"  - {entity['name']}: "
                  f"{entity['total_transactions']} transactions, "
                  f"${entity['total_volume']:.2f} volume")
        
        # Show transaction history
        history = self.logger.get_user_history(self.user_id, limit=10)
        print(f"\n📝 TRANSACTION HISTORY ({len(history)} recent):")
        for tx in history:
            counterparty = tx['counterparty_name'] or 'N/A'
            amount = f"${tx['amount']:.2f}" if tx['amount'] else 'N/A'
            print(f"  - {tx['operation_type']}: {counterparty}, "
                  f"{amount}, {tx['status']}, "
                  f"confidence: {tx['intent_confidence']:.0%}")
        
        # Show operation stats
        stats = self.logger.get_operation_stats(self.user_id)
        print(f"\n📊 OPERATION STATISTICS:")
        for op, data in stats.items():
            print(f"  - {op}: "
                  f"{data['successful']}/{data['count']} successful, "
                  f"avg confidence: {data['avg_confidence']:.0%}")
    
    def cleanup(self):
        """Close database connection"""
        self.db.close()


def main():
    """Run the demonstration"""
    print("=" * 60)
    print("CONVERSATIONAL BANKING SYSTEM - INTEGRATION DEMO")
    print("=" * 60)
    print("\nDemonstrating: IntentParser + EntityManager + TransactionLogger")
    print("Database: demo_banking.db")
    
    # Initialize demo
    demo = ConversationalBankingDemo()
    
    # Test various commands
    test_commands = [
        "I want to issue a check to Alice for $500",
        "Write a check for Bob $1000",
        "Reject any incoming checks from Charlie",
        "Accept the check from Alice",
        "Forward check number 123 to David",
        "Tokenize check 456",
        "Buy token 789",
    ]
    
    print("\n" + "=" * 60)
    print("PROCESSING COMMANDS")
    print("=" * 60)
    
    for command in test_commands:
        demo.process_command(command)
    
    # Show summary
    demo.show_summary()
    
    # Cleanup
    demo.cleanup()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nDatabase file 'demo_banking.db' created with sample data.")
    print("You can inspect it with any SQLite viewer.")


if __name__ == "__main__":
    main()
