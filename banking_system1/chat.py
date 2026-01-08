#!/usr/bin/env python3
"""
Interactive Banking Chat - Hands-On Demo
========================================

Live conversational banking powered by Claude API.
This is the standalone product interface.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser
from managers.check_manager import CheckManager
from managers.transaction_manager import TransactionManager
from managers.conversation_agent import ConversationAgent
import config


class BankingChat:
    """Interactive banking chat interface"""
    
    def __init__(self):
        """Initialize the complete system"""
        print("🏦 Initializing Conversational Banking System...")
        
        # Database setup
        self.db = DatabaseManager(config.DATABASE_PATH)
        self.db.connect()
        self.db.initialize_schema()
        
        # Managers
        self.entity_mgr = EntityManager(self.db)
        self.logger = TransactionLogger(self.db)
        self.parser = IntentParser()
        self.check_mgr = CheckManager(self.db, self.entity_mgr)
        
        # Orchestrator
        self.tx_mgr = TransactionManager(
            self.parser,
            self.check_mgr,
            self.entity_mgr,
            self.logger
        )
        
        # Conversational AI
        self.agent = ConversationAgent(self.tx_mgr)
        
        # Setup demo user
        self.user_id, self.username = self._setup_demo_user()
        
        print("✓ System ready!\n")
    
    def _setup_demo_user(self):
        """Create or get demo user"""
        cursor = self.db.conn.cursor()
        
        # Try to find existing demo user
        cursor.execute("SELECT id, username, balance FROM users WHERE username = 'DemoUser'")
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            username = user['username']
            balance = user['balance']
            print(f"✓ Welcome back, {username}! Balance: ${balance:.2f}")
        else:
            # Create new demo user
            cursor.execute("""
                INSERT INTO users (username, balance)
                VALUES ('DemoUser', ?)
            """, (config.DEFAULT_USER_BALANCE,))
            user_id = cursor.lastrowid
            username = 'DemoUser'
            self.db.conn.commit()
            print(f"✓ Created new account: {username}")
            print(f"✓ Starting balance: ${config.DEFAULT_USER_BALANCE:.2f}")
        
        return user_id, username
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "=" * 70)
        print("🏦  CONVERSATIONAL BANKING SYSTEM - LIVE DEMO")
        print("=" * 70)
        print("\nWelcome to your AI-powered banking assistant!")
        print("Powered by Claude API for natural conversations.\n")
        
        print("💡 What you can do:")
        print("  • Issue checks: 'Issue a check to Alice for $500'")
        print("  • Accept checks: 'Accept the check from Bob'")
        print("  • Deny checks: 'Reject the check from Charlie'")
        print("  • Forward checks: 'Forward check #123 to David'")
        print("  • Check balance: 'What's my balance?'")
        print("  • View checks: 'Show my checks'")
        print("  • View history: 'Show my transaction history'\n")
        
        print("📝 Tips:")
        print("  • Speak naturally - Claude understands you!")
        print("  • Type 'balance' for quick balance check")
        print("  • Type 'checks' to see all your checks")
        print("  • Type 'help' for assistance")
        print("  • Type 'quit' or 'exit' to leave\n")
        
        print("=" * 70)
        print(f"💰 Current Balance: ${self.check_mgr.get_user_balance(self.user_id):.2f}")
        print("=" * 70)
        print()
    
    def run(self):
        """Main chat loop"""
        self.display_welcome()
        
        print("🤖 Assistant: Hi! I'm your banking assistant. How can I help you today?\n")
        
        while True:
            try:
                # Get user input
                user_input = input(f"💬 {self.username}: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\n🤖 Assistant: Goodbye! Thanks for using Conversational Banking.\n")
                    break
                
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                elif user_input.lower() == 'balance':
                    balance = self.check_mgr.get_user_balance(self.user_id)
                    print(f"\n💰 Your balance: ${balance:.2f}\n")
                    continue
                
                elif user_input.lower() == 'checks':
                    self._show_checks()
                    continue
                
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    self.display_welcome()
                    continue
                
                # Process through conversation agent
                print()  # Add spacing
                response = self.agent.chat(self.user_id, user_input, self.username)
                print(f"🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\n🤖 Assistant: Goodbye! Thanks for using Conversational Banking.\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                if config.VERBOSE_LOGGING:
                    import traceback
                    traceback.print_exc()
    
    def _show_help(self):
        """Show help message"""
        print("\n" + "=" * 70)
        print("📚 HELP - Available Commands")
        print("=" * 70)
        print("\n🔹 Banking Operations (speak naturally!):")
        print("  'Issue a check to [name] for $[amount]'")
        print("  'Accept check from [name]' or 'Accept check #[number]'")
        print("  'Deny check from [name]' or 'Deny check #[number]'")
        print("  'Forward check #[number] to [name]'")
        print("\n🔹 Quick Commands:")
        print("  balance  - Show current balance")
        print("  checks   - List all checks")
        print("  help     - Show this help")
        print("  clear    - Clear screen")
        print("  quit     - Exit the system")
        print("\n🔹 Natural Language:")
        print("  You can speak naturally! Try:")
        print("  'What's my balance?'")
        print("  'Show me my checks'")
        print("  'I want to send $200 to Bob'")
        print("=" * 70)
        print()
    
    def _show_checks(self):
        """Show all checks"""
        checks = self.check_mgr.get_user_checks(self.user_id, 'all')
        
        print("\n" + "=" * 70)
        print("📋 YOUR CHECKS")
        print("=" * 70)
        
        if not checks:
            print("\nNo checks found.")
        else:
            # Categorize
            pending_in = [c for c in checks if c['status'] == 'PENDING' and c['payee_id'] == self.user_id]
            issued = [c for c in checks if c['issuer_id'] == self.user_id]
            
            if pending_in:
                print(f"\n🔔 PENDING INCOMING ({len(pending_in)}):")
                for check in pending_in:
                    print(f"  Check #{check['id']}: ${check['amount']:.2f} from {check['issuer_name']}")
            
            if issued:
                print(f"\n📤 ISSUED BY YOU ({len(issued)}):")
                for check in issued:
                    status_icon = "⏳" if check['status'] == 'PENDING' else "✓"
                    print(f"  {status_icon} Check #{check['id']}: ${check['amount']:.2f} to {check['payee_name']} ({check['status']})")
        
        print("=" * 70)
        print()
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.close()


def main():
    """Main entry point"""
    try:
        chat = BankingChat()
        chat.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            chat.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
