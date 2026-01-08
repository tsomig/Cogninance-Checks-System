#!/usr/bin/env python3
"""
Integration Tests
=================

Tests the complete pipeline: IntentParser → TransactionManager → CheckManager → Database
"""

import sys
import os
import tempfile

# Add test environment to path
sys.path.insert(0, '/home/claude/test_env')

from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser
from managers.check_manager import CheckManager
from managers.transaction_manager import TransactionManager


class TestIntegration:
    """Integration test suite"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
        self.setup_system()
    
    def setup_system(self):
        """Initialize complete system"""
        # Temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize all components
        self.db = DatabaseManager(self.temp_db.name)
        self.db.connect()
        self.db.initialize_schema()
        
        self.entity_mgr = EntityManager(self.db)
        self.logger = TransactionLogger(self.db)
        self.parser = IntentParser()
        self.check_mgr = CheckManager(self.db, self.entity_mgr)
        
        self.tx_mgr = TransactionManager(
            self.parser,
            self.check_mgr,
            self.entity_mgr,
            self.logger
        )
        
        # Create test user
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (1, 'TestUser', 10000.0)")
        self.db.conn.commit()
    
    def cleanup(self):
        """Clean up"""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def assert_equal(self, actual, expected, test_name):
        """Custom assertion"""
        self.tests_run += 1
        if actual == expected:
            self.passed += 1
            print(f"  ✅ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {test_name}")
            print(f"     Expected: {expected}")
            print(f"     Got: {actual}")
            return False
    
    def assert_true(self, condition, test_name):
        """Assert true"""
        self.tests_run += 1
        if condition:
            self.passed += 1
            print(f"  ✅ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {test_name}")
            return False
    
    def test_end_to_end_issue_check(self):
        """Test complete flow: natural language → database"""
        print("\n🔄 Test: End-to-End Issue Check")
        
        # Natural language input
        user_input = "Issue a check to Alice for $500"
        
        # Process through system
        result = self.tx_mgr.process_command(1, user_input)
        
        self.assert_true(result['success'], "Command processed successfully")
        self.assert_true('check_id' in result.get('data', {}), "Check ID returned")
        
        # Verify in database
        check_id = result['data']['check_id']
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM checks WHERE id = ?", (check_id,))
        check = cursor.fetchone()
        
        self.assert_equal(check['amount'], 500.0, "Amount stored in database")
        self.assert_equal(check['status'], 'PENDING', "Status is PENDING")
        
        # Verify transaction logged
        history = self.logger.get_user_history(1, limit=10)
        self.assert_true(len(history) > 0, "Transaction logged")
        self.assert_equal(history[0]['operation_type'], 'ISSUE_CHECK', "Correct operation logged")
    
    def test_end_to_end_accept_check(self):
        """Test accepting check through natural language"""
        print("\n🔄 Test: End-to-End Accept Check")
        
        # Setup: Issue a check
        result1 = self.tx_mgr.process_command(1, "Issue check to Bob for $300")
        check_id = result1['data']['check_id']
        
        # Get Bob's ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Bob'")
        bob_id = cursor.fetchone()['id']
        
        # Accept check
        result2 = self.tx_mgr.process_command(bob_id, f"Accept check #{check_id}")
        
        self.assert_true(result2['success'], "Check accepted")
        
        # Verify status changed
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'ACCEPTED', "Status updated to ACCEPTED")
    
    def test_end_to_end_deny_check(self):
        """Test denying check through natural language"""
        print("\n🔄 Test: End-to-End Deny Check")
        
        # Setup: Issue a check
        result1 = self.tx_mgr.process_command(1, "Issue check to Charlie for $200")
        check_id = result1['data']['check_id']
        
        # Get Charlie's ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Charlie'")
        charlie_id = cursor.fetchone()['id']
        
        # Deny check
        result2 = self.tx_mgr.process_command(charlie_id, f"Deny check #{check_id}")
        
        self.assert_true(result2['success'], "Check denied")
        
        # Verify status
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'DENIED', "Status updated to DENIED")
    
    def test_end_to_end_forward_check(self):
        """Test forwarding check through natural language"""
        print("\n🔄 Test: End-to-End Forward Check")
        
        # Setup: Issue and accept check
        result1 = self.tx_mgr.process_command(1, "Issue check to David for $400")
        check_id = result1['data']['check_id']
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'David'")
        david_id = cursor.fetchone()['id']
        
        self.tx_mgr.process_command(david_id, f"Accept check #{check_id}")
        
        # Forward check
        result3 = self.tx_mgr.process_command(david_id, f"Forward check #{check_id} to Eve")
        
        self.assert_true(result3['success'], "Check forwarded")
        
        # Verify original is FORWARDED
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'FORWARDED', "Original check marked FORWARDED")
        
        # Verify new check exists
        new_check_id = result3['data']['new_check_id']
        cursor.execute("SELECT * FROM checks WHERE id = ?", (new_check_id,))
        new_check = cursor.fetchone()
        self.assert_equal(new_check['status'], 'PENDING', "New check is PENDING")
    
    def test_end_to_end_query_balance(self):
        """Test balance query"""
        print("\n🔄 Test: End-to-End Query Balance")
        
        result = self.tx_mgr.process_command(1, "What's my balance?")
        
        self.assert_true(result['success'], "Balance query successful")
        self.assert_true('balance' in result.get('data', {}), "Balance returned")
        self.assert_equal(result['data']['balance'], 10000.0, "Correct balance")
    
    def test_end_to_end_query_checks(self):
        """Test checks query"""
        print("\n🔄 Test: End-to-End Query Checks")
        
        # Issue some checks first
        self.tx_mgr.process_command(1, "Issue check to Alice for $100")
        self.tx_mgr.process_command(1, "Issue check to Bob for $200")
        
        # Query checks
        result = self.tx_mgr.process_command(1, "Show my checks")
        
        self.assert_true(result['success'], "Checks query successful")
        self.assert_true('checks' in result.get('data', {}), "Checks returned")
        self.assert_true(len(result['data']['checks']) >= 2, "At least 2 checks returned")
    
    def test_end_to_end_query_history(self):
        """Test transaction history query"""
        print("\n🔄 Test: End-to-End Query History")
        
        # Perform some operations
        self.tx_mgr.process_command(1, "Issue check to Frank for $150")
        self.tx_mgr.process_command(1, "What's my balance?")
        
        # Query history
        result = self.tx_mgr.process_command(1, "Show my transaction history")
        
        self.assert_true(result['success'], "History query successful")
        self.assert_true('history' in result.get('data', {}), "History returned")
        self.assert_true(len(result['data']['history']) >= 2, "Multiple transactions recorded")
    
    def test_clarification_needed(self):
        """Test system asks for clarification when needed"""
        print("\n🔄 Test: Clarification Request")
        
        # Ambiguous input (missing amount)
        result = self.tx_mgr.process_command(1, "Issue check to Alice")
        
        self.assert_true(not result['success'], "Operation not executed")
        self.assert_true(result.get('needs_clarification', False), "Clarification requested")
        self.assert_true("amount" in result['message'].lower(), "Missing amount mentioned")
    
    def test_layer2_not_available(self):
        """Test Layer 2 operations return appropriate message"""
        print("\n🔄 Test: Layer 2 Not Available")
        
        result = self.tx_mgr.process_command(1, "Tokenize check #123")
        
        self.assert_true(not result['success'], "Operation not executed")
        self.assert_true(result.get('layer2_not_available', False), "Layer 2 flag set")
        self.assert_true("coming soon" in result['message'].lower(), "Appropriate message")
    
    def test_entity_resolution(self):
        """Test automatic entity resolution"""
        print("\n🔄 Test: Entity Resolution")
        
        # Issue checks to multiple people
        self.tx_mgr.process_command(1, "Issue check to Alice for $100")
        self.tx_mgr.process_command(1, "Issue check to alice for $200")  # lowercase
        self.tx_mgr.process_command(1, "Issue check to ALICE for $300")  # uppercase
        
        # Check entities created
        entities = self.entity_mgr.list_entities()
        alice_entities = [e for e in entities if e['name'] == 'Alice']
        
        self.assert_equal(len(alice_entities), 1, "Only one Alice entity created")
        self.assert_true(alice_entities[0]['total_transactions'] >= 3, "All transactions counted")
        self.assert_true(alice_entities[0]['total_volume'] >= 600.0, "Total volume tracked")
    
    def test_transaction_logging(self):
        """Test comprehensive transaction logging"""
        print("\n🔄 Test: Transaction Logging")
        
        # Perform operation
        user_input = "Issue check to Grace for $777"
        result = self.tx_mgr.process_command(1, user_input)
        
        # Check transaction log
        history = self.logger.get_user_history(1, limit=1)
        tx = history[0]
        
        self.assert_equal(tx['operation_type'], 'ISSUE_CHECK', "Operation type logged")
        self.assert_equal(tx['status'], 'SUCCESS', "Status logged")
        self.assert_equal(tx['amount'], 777.0, "Amount logged")
        self.assert_true(user_input in tx['conversation_context'], "Context preserved")
        self.assert_true(tx['intent_confidence'] > 0, "Confidence logged")
    
    def test_multiple_operations_sequence(self):
        """Test sequence of multiple operations"""
        print("\n🔄 Test: Multiple Operations Sequence")
        
        # Complex scenario
        r1 = self.tx_mgr.process_command(1, "Issue check to Helen for $1000")
        self.assert_true(r1['success'], "Step 1: Issue check")
        
        check_id = r1['data']['check_id']
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Helen'")
        helen_id = cursor.fetchone()['id']
        
        r2 = self.tx_mgr.process_command(helen_id, f"Accept check #{check_id}")
        self.assert_true(r2['success'], "Step 2: Accept check")
        
        r3 = self.tx_mgr.process_command(helen_id, f"Forward check #{check_id} to Ivan")
        self.assert_true(r3['success'], "Step 3: Forward check")
        
        # Verify final state
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'FORWARDED', "Original check is FORWARDED")
        
        # Verify transaction log has all operations
        history = self.logger.get_user_history(1, limit=10)
        operations = [tx['operation_type'] for tx in history]
        self.assert_true('ISSUE_CHECK' in operations, "Issue operation logged")
        
        history_helen = self.logger.get_user_history(helen_id, limit=10)
        operations_helen = [tx['operation_type'] for tx in history_helen]
        self.assert_true('ACCEPT_CHECK' in operations_helen, "Accept operation logged")
        self.assert_true('FORWARD_CHECK' in operations_helen, "Forward operation logged")
    
    def run_all_tests(self):
        """Run complete integration test suite"""
        print("\n" + "="*70)
        print("🧪 INTEGRATION TEST SUITE")
        print("="*70)
        
        self.test_end_to_end_issue_check()
        self.test_end_to_end_accept_check()
        self.test_end_to_end_deny_check()
        self.test_end_to_end_forward_check()
        self.test_end_to_end_query_balance()
        self.test_end_to_end_query_checks()
        self.test_end_to_end_query_history()
        self.test_clarification_needed()
        self.test_layer2_not_available()
        self.test_entity_resolution()
        self.test_transaction_logging()
        self.test_multiple_operations_sequence()
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        success_rate = (self.passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*70)
        
        if self.failed == 0:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print(f"⚠️  {self.failed} test(s) need attention")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestIntegration()
    try:
        success = tester.run_all_tests()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Integration test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        tester.cleanup()
        sys.exit(1)
