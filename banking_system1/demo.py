#!/usr/bin/env python3
"""
Automated System Demo
====================

Demonstrates the complete conversational banking system
with Claude API integration. Runs through a complete
workflow automatically.
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser
from managers.check_manager import CheckManager
from managers.transaction_manager import TransactionManager
from managers.conversation_agent import ConversationAgent
import config


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_step(number, description):
    """Print a step header"""
    print(f"\n{'─' * 70}")
    print(f"Step {number}: {description}")
    print('─' * 70)


def simulate_typing(text, delay=0.03):
    """Simulate typing effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


class AutomatedDemo:
    """Automated demonstration of the system"""
    
    def __init__(self):
        """Initialize system"""
        print_section("CONVERSATIONAL BANKING SYSTEM - AUTOMATED DEMO")
        print("🚀 Initializing system components...\n")
        
        # Database
        self.db = DatabaseManager("demo_banking.db")
        self.db.connect()
        self.db.initialize_schema()
        print("  ✓ Database initialized")
        
        # Managers
        self.entity_mgr = EntityManager(self.db)
        self.logger = TransactionLogger(self.db)
        self.parser = IntentParser()
        self.check_mgr = CheckManager(self.db, self.entity_mgr)
        print("  ✓ Managers created")
        
        # Orchestrator
        self.tx_mgr = TransactionManager(
            self.parser,
            self.check_mgr,
            self.entity_mgr,
            self.logger
        )
        print("  ✓ Transaction manager ready")
        
        # Conversation Agent
        self.agent = ConversationAgent(self.tx_mgr)
        print("  ✓ Claude API connected")
        
        # Create demo user
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, balance)
            VALUES (1, 'DemoUser', 10000.0)
        """)
        self.db.conn.commit()
        self.user_id = 1
        self.username = "DemoUser"
        
        print(f"  ✓ Demo user created: {self.username}")
        print(f"  ✓ Starting balance: $10,000.00")
        
        time.sleep(1)
    
    def demo_conversation(self, user_message, step_num, description):
        """Simulate a conversation turn"""
        print_step(step_num, description)
        
        print(f"\n💬 {self.username}: ", end='')
        simulate_typing(user_message, delay=0.02)
        
        print("\n⏳ Processing...")
        time.sleep(0.5)
        
        # Get response
        response = self.agent.chat(self.user_id, user_message, self.username)
        
        print(f"\n🤖 Assistant: ", end='')
        simulate_typing(response, delay=0.015)
        
        time.sleep(1)
    
    def show_system_state(self):
        """Show current system state"""
        print("\n" + "┌" + "─" * 68 + "┐")
        print("│" + " " * 23 + "SYSTEM STATE" + " " * 33 + "│")
        print("└" + "─" * 68 + "┘")
        
        # Balance
        balance = self.check_mgr.get_user_balance(self.user_id)
        print(f"\n💰 Balance: ${balance:.2f}")
        
        # Checks
        checks = self.check_mgr.get_user_checks(self.user_id, 'all')
        pending_in = [c for c in checks if c['status'] == 'PENDING' and c['payee_id'] == self.user_id]
        issued = [c for c in checks if c['issuer_id'] == self.user_id]
        
        print(f"📋 Checks: {len(issued)} issued, {len(pending_in)} pending incoming")
        
        # Recent transactions
        history = self.logger.get_user_history(self.user_id, limit=5)
        print(f"📝 Transactions: {len(history)} in history")
        
        # Entities
        entities = self.entity_mgr.list_entities(limit=10)
        print(f"🏢 Entities: {len(entities)} counterparties")
        
        print()
        time.sleep(1.5)
    
    def run(self):
        """Run the complete demo"""
        
        # Demo conversations
        conversations = [
            (1, "Greeting", "Hi! What can you help me with?"),
            (2, "Issue Check to Alice", "I want to issue a check to Alice for $500"),
            (3, "Check Balance", "What's my balance now?"),
            (4, "Issue Check to Bob", "Send $1000 to Bob"),
            (5, "Issue Check to Charlie", "Write a check for Charlie, $250"),
            (6, "View All Checks", "Show me all my checks"),
            (7, "Ask about Tokenization", "Can I tokenize one of these checks?"),
            (8, "View Transaction History", "Show my transaction history"),
        ]
        
        for step, description, message in conversations:
            self.demo_conversation(message, step, description)
        
        # Final system state
        print_section("FINAL SYSTEM STATE")
        self.show_system_state()
        
        # Summary
        print_section("DEMO SUMMARY")
        
        print("✨ What we demonstrated:")
        print("  ✓ Natural language understanding (Claude API)")
        print("  ✓ Check issuance with multiple counterparties")
        print("  ✓ Balance queries")
        print("  ✓ Check status viewing")
        print("  ✓ Transaction history tracking")
        print("  ✓ Layer 2 awareness (tokenization coming soon)")
        print("  ✓ Complete audit trail")
        print()
        
        print("🏗️  System Architecture:")
        print("  • IntentParser: Natural language → operations")
        print("  • CheckManager: Layer 1 banking operations")
        print("  • EntityManager: Counterparty management")
        print("  • TransactionLogger: Complete audit trail")
        print("  • ConversationAgent: Claude API integration")
        print("  • TransactionManager: Orchestration layer")
        print()
        
        print("📊 Performance:")
        stats = self.logger.get_operation_stats(self.user_id)
        for op, data in stats.items():
            success_rate = (data['successful'] / data['count'] * 100) if data['count'] > 0 else 0
            print(f"  • {op}: {data['successful']}/{data['count']} ({success_rate:.0f}% success)")
        print()
        
        print("🎯 What's Next:")
        print("  1. Run: python chat.py (for interactive demo)")
        print("  2. Try natural language commands")
        print("  3. Explore check operations")
        print("  4. Watch Claude API in action!")
        print()
        
        print("=" * 70)
        print("🎉 Demo Complete! The system is ready for hands-on use.")
        print("=" * 70)
        print()
    
    def cleanup(self):
        """Cleanup"""
        self.db.close()


def main():
    """Main entry point"""
    try:
        demo = AutomatedDemo()
        demo.run()
        demo.cleanup()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
