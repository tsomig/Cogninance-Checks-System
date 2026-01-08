#!/usr/bin/env python3
"""
================================================================================
CHECK ACCEPTANCE, DENIAL & FORWARDING WORKFLOW DEMO
================================================================================

A comprehensive demonstration of the postdated check lifecycle management system.
This version integrates with the existing banking system modules.

BEHAVIORAL FINANCE CONTEXT:
--------------------------
In traditional banking, checks represent a "promise to pay" - a deferred payment
instrument. The decision to ACCEPT, DENY, or FORWARD a check involves several
behavioral economics considerations:

1. ACCEPT: The payee agrees to receive funds at maturity. This decision may be
   influenced by:
   - Trust in the issuer's creditworthiness
   - Urgency of cash flow needs
   - Relationship value with the counterparty

2. DENY: The payee rejects the check. Reasons may include:
   - Insufficient trust in issuer
   - Dispute over underlying transaction
   - Strategic negotiation leverage

3. FORWARD: The payee transfers rights to a third party. This creates a
   secondary market dynamic where:
   - Original value may be discounted for immediate liquidity
   - Risk is transferred along with potential reward
   - Creates multi-party financial relationships

This script demonstrates these operations in a conversational banking context.

USAGE:
------
    python accept_forward_demo.py

INTEGRATION:
-----------
    This script uses the existing project modules:
    - database.schema (DatabaseManager, EntityManager, TransactionLogger)
    - managers.check_manager (CheckManager)
    - config (DATABASE_PATH, DEFAULT_USER_BALANCE)

AUTHOR: Computational Behavioral Finance Lab
================================================================================
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ============================================================================
# PATH SETUP - Ensure project modules are importable
# ============================================================================

# Add parent directory to path for imports when running from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# PROJECT MODULE IMPORTS
# ============================================================================

try:
    from database.schema import DatabaseManager, EntityManager, TransactionLogger
    from managers.check_manager import CheckManager
    import config
    
    MODULES_AVAILABLE = True
    print("✓ Project modules loaded successfully")
    
except ImportError as e:
    print(f"⚠ Warning: Could not import project modules: {e}")
    print("  Make sure you're running from the banking_system directory")
    print("  or that the modules are in your Python path.")
    MODULES_AVAILABLE = False
    sys.exit(1)


# ============================================================================
# CONFIGURATION (from project config)
# ============================================================================

DATABASE_PATH = getattr(config, 'DATABASE_PATH', 'banking_system.db')
DEFAULT_USER_BALANCE = getattr(config, 'DEFAULT_USER_BALANCE', 10000.0)
DEFAULT_MATURITY_DAYS = 30


# ============================================================================
# DATA MODELS (for enhanced display)
# ============================================================================

@dataclass
class CheckDisplay:
    """
    Enhanced check representation for display purposes.
    Wraps the dictionary returned by CheckManager for easier handling.
    """
    id: int
    issuer_id: int
    issuer_name: str
    payee_id: int
    payee_name: str
    amount: float
    status: str
    issued_at: datetime
    maturity_date: Optional[datetime]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CheckDisplay':
        """Create CheckDisplay from CheckManager dictionary result"""
        maturity = None
        if data.get('maturity_date'):
            try:
                maturity = datetime.fromisoformat(str(data['maturity_date']))
            except (ValueError, TypeError):
                maturity = None
        
        issued = datetime.now()
        if data.get('issued_at'):
            try:
                issued = datetime.fromisoformat(str(data['issued_at']))
            except (ValueError, TypeError):
                pass
        
        return cls(
            id=data['id'],
            issuer_id=data['issuer_id'],
            issuer_name=data.get('issuer_name', 'Unknown'),
            payee_id=data['payee_id'],
            payee_name=data.get('payee_name', 'Unknown'),
            amount=float(data['amount']),
            status=data['status'],
            issued_at=issued,
            maturity_date=maturity
        )
    
    @property
    def days_to_maturity(self) -> int:
        """Calculate remaining days until maturity"""
        if not self.maturity_date:
            return 0
        delta = self.maturity_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def is_matured(self) -> bool:
        """Check if the check has reached maturity"""
        if not self.maturity_date:
            return False
        return datetime.now() >= self.maturity_date
    
    @property
    def maturity_str(self) -> str:
        """Formatted maturity date string"""
        if self.maturity_date:
            return self.maturity_date.strftime('%B %d, %Y')
        return "Not specified"
    
    def __str__(self) -> str:
        return (
            f"Check #{self.id}: ${self.amount:.2f} from {self.issuer_name} "
            f"[{self.status}] - Matures: {self.maturity_str}"
        )


# ============================================================================
# INTERACTIVE WORKFLOW DEMO
# ============================================================================

class InteractiveWorkflowDemo:
    """
    Interactive demonstration of the check acceptance/denial/forwarding workflow.
    
    This class provides a menu-driven interface for users to:
    1. View pending incoming checks
    2. Accept or deny checks
    3. Forward accepted checks to third parties
    4. View transaction history
    
    Uses the existing project modules:
    - DatabaseManager for database operations
    - EntityManager for counterparty management
    - CheckManager for check operations
    - TransactionLogger for audit trail
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the demo with project components.
        
        Args:
            db_path: Optional database path (defaults to config.DATABASE_PATH)
        """
        self.db_path = db_path or DATABASE_PATH
        
        # Initialize database
        self.db = DatabaseManager(self.db_path)
        self.db.connect()
        self.db.initialize_schema()
        
        # Initialize managers (using existing project classes)
        self.entity_mgr = EntityManager(self.db)
        self.logger = TransactionLogger(self.db)
        self.check_mgr = CheckManager(self.db, self.entity_mgr)
        
        self.current_user_id = None
        self.current_username = None
    
    def setup_demo_scenario(self) -> None:
        """
        Create a realistic demo scenario with multiple issuers and checks.
        
        This simulates a business receiving checks from various counterparties
        with different amounts and maturity dates.
        """
        print("\n" + "=" * 70)
        print("SETTING UP DEMO SCENARIO")
        print("=" * 70)
        
        # Create or get the main demo user
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, username, balance FROM users WHERE username = 'WebDemoUser'")
        user = cursor.fetchone()
        
        if user:
            self.current_user_id = user['id']
            self.current_username = user['username']
            balance = user['balance']
            print(f"✓ Welcome back, {self.current_username}! Balance: ${balance:.2f}")
        else:
            cursor.execute("""
                INSERT INTO users (username, balance)
                VALUES ('WebDemoUser', ?)
            """, (DEFAULT_USER_BALANCE,))
            self.current_user_id = cursor.lastrowid
            self.current_username = 'WebDemoUser'
            self.db.conn.commit()
            print(f"✓ Created demo user: {self.current_username}")
            print(f"✓ Starting balance: ${DEFAULT_USER_BALANCE:.2f}")
        
        # Check if we already have pending checks
        existing_checks = self.check_mgr.get_user_checks(self.current_user_id, 'pending')
        
        if existing_checks:
            print(f"\n✓ Found {len(existing_checks)} existing pending checks")
            print("  (Use option [5] from main menu to reset scenario)")
            return
        
        # Create various issuers (counterparties) with checks
        issuers_data = [
            ("Alice Corporation", 1500.00, 15),   # Corporate client, short term
            ("Bob's Trading Co", 3200.00, 30),    # Trading partner, standard term
            ("Charlie Suppliers", 750.00, 45),    # Supplier, extended term
            ("Diana Investments", 5000.00, 60),   # Investment, long term
            ("Echo Enterprises", 2100.00, 20),    # Enterprise client, short term
        ]
        
        print("\nCreating incoming checks from various issuers:")
        print("-" * 50)
        
        for issuer_name, amount, maturity_days in issuers_data:
            # Create issuer user account
            issuer_entity_id = self.entity_mgr.get_or_create_entity(issuer_name, 'USER')
            
            # Get or create issuer user
            cursor.execute("SELECT id FROM users WHERE username = ?", (issuer_name,))
            issuer_row = cursor.fetchone()
            
            if issuer_row:
                issuer_id = issuer_row['id']
            else:
                cursor.execute(
                    "INSERT INTO users (username, balance) VALUES (?, ?)",
                    (issuer_name, 50000.0)
                )
                issuer_id = cursor.lastrowid
                self.db.conn.commit()
            
            # Issue check FROM the issuer TO the demo user
            # We need to create the check directly since check_mgr.issue_check
            # is designed for the current user to issue TO someone
            maturity_date = datetime.now() + timedelta(days=maturity_days)
            
            cursor.execute("""
                INSERT INTO checks (issuer_id, payee_id, amount, status, maturity_date)
                VALUES (?, ?, ?, 'PENDING', ?)
            """, (issuer_id, self.current_user_id, amount, maturity_date.isoformat()))
            check_id = cursor.lastrowid
            self.db.conn.commit()
            
            print(f"  • Check #{check_id}: ${amount:,.2f} from {issuer_name}")
            print(f"    Matures: {maturity_date.strftime('%B %d, %Y')} ({maturity_days} days)")
        
        # Create some potential forward recipients
        forward_recipients = ["Vendor One", "Partner Alpha", "Service Provider"]
        for name in forward_recipients:
            self.entity_mgr.get_or_create_entity(name, 'USER')
        
        print("\n✓ Demo scenario ready!")
        print(f"  Total pending checks: {len(issuers_data)}")
        print(f"  Potential forward recipients created: {len(forward_recipients)}")
    
    def get_pending_checks(self) -> List[CheckDisplay]:
        """Get all pending incoming checks as CheckDisplay objects"""
        checks_data = self.check_mgr.get_user_checks(self.current_user_id, 'all')
        
        # Filter for pending checks where current user is payee
        pending = [
            CheckDisplay.from_dict(c) 
            for c in checks_data 
            if c['status'] == 'PENDING' and c['payee_id'] == self.current_user_id
        ]
        
        # Sort by maturity date
        pending.sort(key=lambda x: x.maturity_date or datetime.max)
        return pending
    
    def get_accepted_checks(self) -> List[CheckDisplay]:
        """Get all accepted checks available for forwarding"""
        checks_data = self.check_mgr.get_user_checks(self.current_user_id, 'all')
        
        # Filter for accepted checks where current user is payee
        accepted = [
            CheckDisplay.from_dict(c) 
            for c in checks_data 
            if c['status'] == 'ACCEPTED' and c['payee_id'] == self.current_user_id
        ]
        
        # Sort by maturity date
        accepted.sort(key=lambda x: x.maturity_date or datetime.max)
        return accepted
    
    def display_pending_checks(self) -> List[CheckDisplay]:
        """Display all pending incoming checks with analysis"""
        checks = self.get_pending_checks()
        
        print("\n" + "=" * 70)
        print("📥 PENDING INCOMING CHECKS")
        print("=" * 70)
        
        if not checks:
            print("\n  No pending checks to review.")
            return []
        
        total_value = sum(c.amount for c in checks)
        print(f"\n  Total pending value: ${total_value:,.2f}")
        print(f"  Number of checks: {len(checks)}")
        print("-" * 70)
        
        for i, check in enumerate(checks, 1):
            print(f"\n  [{i}] Check #{check.id}")
            print(f"      Amount:     ${check.amount:,.2f}")
            print(f"      From:       {check.issuer_name}")
            print(f"      Issued:     {check.issued_at.strftime('%B %d, %Y')}")
            print(f"      Matures:    {check.maturity_str}")
            print(f"      Days left:  {check.days_to_maturity}")
        
        print("-" * 70)
        return checks
    
    def display_accepted_checks(self) -> List[CheckDisplay]:
        """Display all accepted checks available for forwarding"""
        checks = self.get_accepted_checks()
        
        print("\n" + "=" * 70)
        print("✓ ACCEPTED CHECKS (Available for Forwarding)")
        print("=" * 70)
        
        if not checks:
            print("\n  No accepted checks available for forwarding.")
            return []
        
        total_value = sum(c.amount for c in checks)
        print(f"\n  Total accepted value: ${total_value:,.2f}")
        print("-" * 70)
        
        for i, check in enumerate(checks, 1):
            print(f"\n  [{i}] Check #{check.id}")
            print(f"      Amount:     ${check.amount:,.2f}")
            print(f"      From:       {check.issuer_name}")
            print(f"      Matures:    {check.maturity_str}")
            print(f"      Days left:  {check.days_to_maturity}")
        
        print("-" * 70)
        return checks
    
    def process_check_decision(self) -> None:
        """
        Interactive loop for accepting/denying pending checks.
        
        BEHAVIORAL FINANCE INSIGHT:
        ---------------------------
        This implements the core decision workflow where users evaluate
        each incoming check and make acceptance decisions. The decision
        process involves:
        
        - Temporal discounting: Is the wait to maturity acceptable?
        - Counterparty risk assessment: Do I trust the issuer?
        - Opportunity cost: What else could I do with this commitment?
        """
        while True:
            checks = self.display_pending_checks()
            
            if not checks:
                print("\n  All pending checks have been processed.")
                break
            
            print("\n  OPTIONS:")
            print("  ─────────")
            print(f"  Enter check number (1-{len(checks)}) to review")
            print("  [A] Accept all pending checks")
            print("  [S] Skip to forwarding")
            print("  [Q] Quit to main menu")
            
            choice = input("\n  Your choice: ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice == 'S':
                return  # Skip to forwarding workflow
            elif choice == 'A':
                # Accept all pending checks
                for check in checks:
                    success, msg, _ = self.check_mgr.accept_check(
                        self.current_user_id, 
                        check_id=check.id
                    )
                    print(f"  {msg}")
                print("\n  ✓ All checks processed!")
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(checks):
                    self._handle_single_check(checks[idx])
                else:
                    print("  ⚠ Invalid selection")
            else:
                print("  ⚠ Invalid input")
    
    def _handle_single_check(self, check: CheckDisplay) -> None:
        """
        Handle decision for a single check.
        
        BEHAVIORAL FINANCE INSIGHT:
        ---------------------------
        Individual check review allows for nuanced decision-making:
        - Larger amounts may warrant more scrutiny
        - Shorter maturities reduce temporal risk
        - Known counterparties may receive preferential treatment
        """
        print("\n" + "─" * 50)
        print(f"  REVIEWING: Check #{check.id}")
        print("─" * 50)
        print(f"  Amount:    ${check.amount:,.2f}")
        print(f"  From:      {check.issuer_name}")
        print(f"  Matures:   {check.maturity_str}")
        print(f"  Days left: {check.days_to_maturity}")
        print()
        print("  [A] Accept this check")
        print("  [D] Deny this check")
        print("  [B] Go back")
        
        while True:
            decision = input("\n  Decision: ").strip().upper()
            
            if decision == 'A':
                success, msg, _ = self.check_mgr.accept_check(
                    self.current_user_id, 
                    check_id=check.id
                )
                print(f"\n  {msg}")
                break
            elif decision == 'D':
                success, msg, _ = self.check_mgr.deny_check(
                    self.current_user_id, 
                    check_id=check.id
                )
                print(f"\n  {msg}")
                break
            elif decision == 'B':
                break
            else:
                print("  ⚠ Please enter A, D, or B")
    
    def process_forwarding(self) -> None:
        """
        Interactive loop for forwarding accepted checks.
        
        BEHAVIORAL FINANCE INSIGHT:
        ---------------------------
        Forwarding creates a secondary market mechanism:
        
        1. LIQUIDITY TRANSFORMATION
           Convert future payment into immediate economic value
           
        2. RISK TRANSFER
           Original payee offloads issuer default risk
           
        3. RELATIONSHIP ARBITRAGE
           Use check as payment to own creditors
           
        4. MATURITY MATCHING
           Align cash flows with own obligations
        """
        while True:
            checks = self.display_accepted_checks()
            
            if not checks:
                break
            
            print("\n  OPTIONS:")
            print("  ─────────")
            print(f"  Enter check number (1-{len(checks)}) to forward")
            print("  [Q] Return to main menu")
            
            choice = input("\n  Your choice: ").strip().upper()
            
            if choice == 'Q':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(checks):
                    self._handle_forward(checks[idx])
                else:
                    print("  ⚠ Invalid selection")
            else:
                print("  ⚠ Invalid input")
    
    def _handle_forward(self, check: CheckDisplay) -> None:
        """
        Handle forwarding of a single check.
        
        Uses the existing CheckManager.forward_check() method.
        """
        print("\n" + "─" * 50)
        print(f"  FORWARDING: Check #{check.id}")
        print("─" * 50)
        print(f"  Amount:    ${check.amount:,.2f}")
        print(f"  From:      {check.issuer_name}")
        print(f"  Matures:   {check.maturity_str}")
        print()
        
        recipient = input("  Forward to (name): ").strip()
        
        if not recipient:
            print("  ⚠ Forwarding cancelled")
            return
        
        # Confirm the forward
        print(f"\n  Confirm forward of ${check.amount:,.2f} to {recipient}?")
        confirm = input("  [Y]es / [N]o: ").strip().upper()
        
        if confirm == 'Y':
            success, msg, new_id = self.check_mgr.forward_check(
                self.current_user_id, 
                check.id, 
                recipient
            )
            print(f"\n  {msg}")
        else:
            print("  ⚠ Forwarding cancelled")
    
    def display_transaction_history(self) -> None:
        """Display the transaction audit log using TransactionLogger"""
        history = self.logger.get_user_history(self.current_user_id, limit=20)
        
        print("\n" + "=" * 70)
        print("📋 TRANSACTION HISTORY")
        print("=" * 70)
        
        if not history:
            print("\n  No transactions recorded.")
            return
        
        for record in history:
            timestamp = record.get('timestamp', 'Unknown time')
            operation = record.get('operation_type', 'Unknown')
            status = record.get('status', 'Unknown')
            counterparty = record.get('counterparty_name', 'N/A')
            amount = record.get('amount')
            
            print(f"\n  {timestamp}")
            print(f"  Operation: {operation} - {status}")
            if counterparty and counterparty != 'N/A':
                print(f"  Counterparty: {counterparty}")
            if amount:
                print(f"  Amount: ${amount:.2f}")
            print("  " + "─" * 40)
    
    def display_all_checks_summary(self) -> None:
        """Display a comprehensive summary of all checks"""
        all_checks = self.check_mgr.get_user_checks(self.current_user_id, 'all')
        
        print("\n" + "=" * 70)
        print("📊 COMPLETE CHECK SUMMARY")
        print("=" * 70)
        
        if not all_checks:
            print("\n  No checks found.")
            return
        
        # Categorize checks
        pending_in = [c for c in all_checks if c['status'] == 'PENDING' and c['payee_id'] == self.current_user_id]
        accepted = [c for c in all_checks if c['status'] == 'ACCEPTED' and c['payee_id'] == self.current_user_id]
        denied = [c for c in all_checks if c['status'] == 'DENIED' and c['payee_id'] == self.current_user_id]
        forwarded = [c for c in all_checks if c['status'] == 'FORWARDED']
        issued = [c for c in all_checks if c['issuer_id'] == self.current_user_id]
        
        print(f"\n  📥 Pending Incoming:  {len(pending_in):>3} checks  (${sum(c['amount'] for c in pending_in):>12,.2f})")
        print(f"  ✓  Accepted:          {len(accepted):>3} checks  (${sum(c['amount'] for c in accepted):>12,.2f})")
        print(f"  ✗  Denied:            {len(denied):>3} checks  (${sum(c['amount'] for c in denied):>12,.2f})")
        print(f"  ➜  Forwarded:         {len(forwarded):>3} checks  (${sum(c['amount'] for c in forwarded):>12,.2f})")
        print(f"  📤 Issued by you:     {len(issued):>3} checks  (${sum(c['amount'] for c in issued):>12,.2f})")
        print("-" * 70)
        print(f"  Total checks: {len(all_checks)}")
    
    def reset_demo_scenario(self) -> None:
        """Reset the demo by clearing existing checks and creating new ones"""
        print("\n  ⚠ This will delete all existing checks for demo user.")
        confirm = input("  Continue? [Y]es / [N]o: ").strip().upper()
        
        if confirm != 'Y':
            print("  Reset cancelled.")
            return
        
        cursor = self.db.conn.cursor()
        
        # Delete checks where demo user is involved
        cursor.execute("""
            DELETE FROM checks 
            WHERE issuer_id = ? OR payee_id = ?
        """, (self.current_user_id, self.current_user_id))
        
        # Clear transaction history for demo user
        cursor.execute("""
            DELETE FROM transaction_history 
            WHERE user_id = ?
        """, (self.current_user_id,))
        
        self.db.conn.commit()
        print("  ✓ Cleared existing data")
        
        # Re-create scenario
        self.setup_demo_scenario()
    
    def run_main_menu(self) -> None:
        """Main interactive menu loop"""
        print("\n" + "=" * 70)
        print("MAIN MENU")
        print("=" * 70)
        
        while True:
            print(f"\n  Logged in as: {self.current_username}")
            print("\n  What would you like to do?")
            print("  ─────────────────────────")
            print("  [1] View & Process Pending Checks (Accept/Deny)")
            print("  [2] Forward Accepted Checks")
            print("  [3] View Check Summary")
            print("  [4] View Transaction History")
            print("  [5] Reset Demo Scenario")
            print("  [Q] Quit")
            
            choice = input("\n  Your choice: ").strip().upper()
            
            if choice == '1':
                self.process_check_decision()
            elif choice == '2':
                self.process_forwarding()
            elif choice == '3':
                self.display_all_checks_summary()
            elif choice == '4':
                self.display_transaction_history()
            elif choice == '5':
                self.reset_demo_scenario()
            elif choice == 'Q':
                print("\n  Thank you for using the Check Workflow Demo!")
                break
            else:
                print("  ⚠ Invalid selection")
    
    def run(self) -> None:
        """Main entry point for the demo"""
        try:
            print("\n" + "=" * 70)
            print("╔══════════════════════════════════════════════════════════════════╗")
            print("║     CHECK ACCEPTANCE, DENIAL & FORWARDING WORKFLOW DEMO          ║")
            print("║     ─────────────────────────────────────────────────────        ║")
            print("║     Integrated with Banking System Modules                       ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            
            self.setup_demo_scenario()
            self.run_main_menu()
            
        except KeyboardInterrupt:
            print("\n\n  Demo interrupted by user.")
        finally:
            self.db.close()
            print("  Database connection closed.")


# ============================================================================
# PROGRAMMATIC API DEMO
# ============================================================================

def programmatic_demo():
    """
    Demonstrates the workflow programmatically without user interaction.
    
    This version uses the actual project CheckManager methods:
    - issue_check()
    - accept_check()
    - deny_check()
    - forward_check()
    
    Useful for:
    - Automated testing
    - Integration examples
    - Understanding the API
    """
    print("\n" + "=" * 70)
    print("PROGRAMMATIC API DEMONSTRATION")
    print("(Using existing project modules)")
    print("=" * 70)
    
    # Initialize using project components
    db = DatabaseManager(DATABASE_PATH)
    db.connect()
    db.initialize_schema()
    
    entity_mgr = EntityManager(db)
    logger = TransactionLogger(db)
    check_mgr = CheckManager(db, entity_mgr)
    
    try:
        cursor = db.conn.cursor()
        
        # Create test users
        print("\n1. Creating test users...")
        
        test_users = {}
        for name, balance in [("ApiAlice", 10000.0), ("ApiBob", 5000.0), ("ApiCharlie", 3000.0)]:
            cursor.execute("SELECT id FROM users WHERE username = ?", (name,))
            row = cursor.fetchone()
            if row:
                test_users[name] = row['id']
            else:
                cursor.execute("INSERT INTO users (username, balance) VALUES (?, ?)", (name, balance))
                test_users[name] = cursor.lastrowid
        db.conn.commit()
        
        print(f"   Created/Found: {', '.join(test_users.keys())}")
        
        # Alice issues checks to Bob using CheckManager
        print("\n2. Alice issues checks to Bob...")
        
        # First, we need to create checks FROM Alice TO Bob
        # Since check_mgr.issue_check takes issuer_id and payee_name,
        # we can use it directly from Alice's perspective
        
        alice_id = test_users["ApiAlice"]
        bob_id = test_users["ApiBob"]
        charlie_id = test_users["ApiCharlie"]
        
        # Create check directly (simulating Alice issuing to Bob)
        maturity1 = datetime.now() + timedelta(days=30)
        maturity2 = datetime.now() + timedelta(days=15)
        
        cursor.execute("""
            INSERT INTO checks (issuer_id, payee_id, amount, status, maturity_date)
            VALUES (?, ?, ?, 'PENDING', ?)
        """, (alice_id, bob_id, 1000.00, maturity1.isoformat()))
        check1_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO checks (issuer_id, payee_id, amount, status, maturity_date)
            VALUES (?, ?, ?, 'PENDING', ?)
        """, (alice_id, bob_id, 500.00, maturity2.isoformat()))
        check2_id = cursor.lastrowid
        db.conn.commit()
        
        print(f"   Issued: Check #{check1_id} ($1000, 30 days), Check #{check2_id} ($500, 15 days)")
        
        # Bob views pending checks
        print("\n3. Bob views pending checks...")
        pending = check_mgr.get_user_checks(bob_id, 'pending')
        for check in pending:
            print(f"   • Check #{check['id']}: ${check['amount']} from User #{check['issuer_id']}")
        
        # Bob accepts the first check
        print(f"\n4. Bob accepts Check #{check1_id}...")
        success, msg, _ = check_mgr.accept_check(bob_id, check_id=check1_id)
        print(f"   {msg}")
        
        # Bob denies the second check
        print(f"\n5. Bob denies Check #{check2_id}...")
        success, msg, _ = check_mgr.deny_check(bob_id, check_id=check2_id)
        print(f"   {msg}")
        
        # Bob forwards the accepted check to Charlie
        print(f"\n6. Bob forwards Check #{check1_id} to ApiCharlie...")
        success, msg, new_id = check_mgr.forward_check(bob_id, check1_id, "ApiCharlie")
        print(f"   {msg}")
        
        # Charlie views their pending check
        print("\n7. ApiCharlie views pending checks...")
        charlie_pending = check_mgr.get_user_checks(charlie_id, 'pending')
        for check in charlie_pending:
            if check['payee_id'] == charlie_id and check['status'] == 'PENDING':
                print(f"   • Check #{check['id']}: ${check['amount']} from User #{check['issuer_id']}")
        
        # Show transaction history
        print("\n8. Bob's transaction history...")
        history = logger.get_user_history(bob_id, limit=5)
        for record in history:
            print(f"   • {record['operation_type']}: {record['status']}")
        
        print("\n" + "=" * 70)
        print("PROGRAMMATIC DEMO COMPLETE")
        print("=" * 70)
        
    finally:
        db.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point with mode selection"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "WORKFLOW DEMO LAUNCHER" + " " * 26 + "║")
    print("║" + " " * 15 + "(Integrated with Project Modules)" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\n  Select demo mode:")
    print("  ─────────────────")
    print("  [1] Interactive Mode (menu-driven workflow)")
    print("  [2] Programmatic Mode (API demonstration)")
    print("  [Q] Quit")
    
    choice = input("\n  Your choice: ").strip().upper()
    
    if choice == '1':
        demo = InteractiveWorkflowDemo()
        demo.run()
    elif choice == '2':
        programmatic_demo()
    elif choice == 'Q':
        print("\n  Goodbye!")
    else:
        print("\n  Invalid selection. Running interactive mode by default...")
        demo = InteractiveWorkflowDemo()
        demo.run()


if __name__ == "__main__":
    main()
