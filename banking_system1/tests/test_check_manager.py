#!/usr/bin/env python3
"""
Unit Tests for CheckManager
===========================

Tests all Layer 1 check operations with database integration.
"""

import sys
import os
import tempfile

# Add test environment to path
sys.path.insert(0, '/home/claude/test_env')

from database.schema import DatabaseManager, EntityManager
from managers.check_manager import CheckManager


class TestCheckManager:
    """Test suite for CheckManager"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
        self.setup_test_db()
    
    def setup_test_db(self):
        """Create a temporary test database"""
        # Use temporary file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database
        self.db = DatabaseManager(self.temp_db.name)
        self.db.connect()
        self.db.initialize_schema()
        
        # Create managers
        self.entity_mgr = EntityManager(self.db)
        self.check_mgr = CheckManager(self.db, self.entity_mgr)
        
        # Create test users
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (1, 'TestUser1', 10000.0)")
        cursor.execute("INSERT INTO users (id, username, balance) VALUES (2, 'TestUser2', 5000.0)")
        self.db.conn.commit()
    
    def cleanup(self):
        """Clean up test database"""
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
    
    def assert_not_none(self, value, test_name):
        """Assert not None"""
        return self.assert_true(value is not None, test_name)
    
    def test_issue_check_success(self):
        """Test successful check issuance"""
        print("\n💰 Test: Issue Check (Success)")
        
        success, message, check_id = self.check_mgr.issue_check(
            issuer_id=1,
            payee_name="Alice",
            amount=500.0
        )
        
        self.assert_true(success, "Check issued successfully")
        self.assert_not_none(check_id, "Check ID generated")
        self.assert_true("issued" in message.lower(), "Success message received")
        
        # Verify in database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM checks WHERE id = ?", (check_id,))
        check = cursor.fetchone()
        
        self.assert_equal(check['amount'], 500.0, "Amount stored correctly")
        self.assert_equal(check['status'], 'PENDING', "Status is PENDING")
        self.assert_not_none(check['maturity_date'], "Maturity date set")
    
    def test_issue_check_invalid_issuer(self):
        """Test check issuance with invalid issuer"""
        print("\n💰 Test: Issue Check (Invalid Issuer)")
        
        success, message, check_id = self.check_mgr.issue_check(
            issuer_id=999,  # Non-existent user
            payee_name="Alice",
            amount=500.0
        )
        
        self.assert_true(not success, "Check issuance failed")
        self.assert_true(check_id is None, "No check ID generated")
        self.assert_true("not found" in message.lower(), "Error message explains issue")
    
    def test_issue_check_creates_payee(self):
        """Test that issuing check creates payee user if needed"""
        print("\n💰 Test: Issue Check (Auto-create Payee)")
        
        success, message, check_id = self.check_mgr.issue_check(
            issuer_id=1,
            payee_name="NewPerson",
            amount=750.0
        )
        
        self.assert_true(success, "Check issued successfully")
        
        # Verify payee was created
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ("NewPerson",))
        payee = cursor.fetchone()
        
        self.assert_not_none(payee, "Payee user created automatically")
        self.assert_equal(payee['balance'], 0.0, "New payee has zero balance")
    
    def test_accept_check_by_id(self):
        """Test accepting check by check ID"""
        print("\n✅ Test: Accept Check (By ID)")
        
        # First, issue a check
        success, _, check_id = self.check_mgr.issue_check(1, "Bob", 300.0)
        self.assert_true(success, "Setup: Check issued")
        
        # Get Bob's user ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Bob'")
        bob_id = cursor.fetchone()['id']
        
        # Accept the check
        success, message, accepted_id = self.check_mgr.accept_check(
            user_id=bob_id,
            check_id=check_id
        )
        
        self.assert_true(success, "Check accepted successfully")
        self.assert_equal(accepted_id, check_id, "Correct check ID returned")
        
        # Verify status changed
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'ACCEPTED', "Status changed to ACCEPTED")
    
    def test_accept_check_by_issuer_name(self):
        """Test accepting check by issuer name"""
        print("\n✅ Test: Accept Check (By Issuer Name)")
        
        # Issue check from TestUser1
        success, _, check_id = self.check_mgr.issue_check(1, "Charlie", 400.0)
        self.assert_true(success, "Setup: Check issued")
        
        # Get Charlie's user ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Charlie'")
        charlie_id = cursor.fetchone()['id']
        
        # Accept by issuer name
        success, message, accepted_id = self.check_mgr.accept_check(
            user_id=charlie_id,
            issuer_name="TestUser1"
        )
        
        self.assert_true(success, "Check accepted by issuer name")
        self.assert_equal(accepted_id, check_id, "Correct check ID returned")
    
    def test_accept_check_not_pending(self):
        """Test that only PENDING checks can be accepted"""
        print("\n✅ Test: Accept Check (Not Pending)")
        
        # Issue and accept check
        success, _, check_id = self.check_mgr.issue_check(1, "David", 200.0)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'David'")
        david_id = cursor.fetchone()['id']
        
        self.check_mgr.accept_check(david_id, check_id)
        
        # Try to accept again
        success, message, _ = self.check_mgr.accept_check(david_id, check_id)
        
        self.assert_true(not success, "Cannot accept already-accepted check")
        self.assert_true("not found" in message.lower() or "no pending" in message.lower(), 
                        "Appropriate error message")
    
    def test_deny_check_by_id(self):
        """Test denying check by check ID"""
        print("\n❌ Test: Deny Check (By ID)")
        
        # Issue check
        success, _, check_id = self.check_mgr.issue_check(1, "Eve", 600.0)
        self.assert_true(success, "Setup: Check issued")
        
        # Get Eve's user ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Eve'")
        eve_id = cursor.fetchone()['id']
        
        # Deny the check
        success, message, denied_id = self.check_mgr.deny_check(
            user_id=eve_id,
            check_id=check_id
        )
        
        self.assert_true(success, "Check denied successfully")
        self.assert_equal(denied_id, check_id, "Correct check ID returned")
        
        # Verify status
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'DENIED', "Status changed to DENIED")
    
    def test_deny_check_by_issuer_name(self):
        """Test denying check by issuer name"""
        print("\n❌ Test: Deny Check (By Issuer Name)")
        
        # Issue check
        success, _, check_id = self.check_mgr.issue_check(1, "Frank", 800.0)
        self.assert_true(success, "Setup: Check issued")
        
        # Get Frank's user ID
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Frank'")
        frank_id = cursor.fetchone()['id']
        
        # Deny by issuer name
        success, message, denied_id = self.check_mgr.deny_check(
            user_id=frank_id,
            issuer_name="TestUser1"
        )
        
        self.assert_true(success, "Check denied by issuer name")
    
    def test_forward_check(self):
        """Test forwarding an accepted check"""
        print("\n➡️  Test: Forward Check")
        
        # Issue and accept check
        success, _, check_id = self.check_mgr.issue_check(1, "Grace", 1000.0)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Grace'")
        grace_id = cursor.fetchone()['id']
        
        self.check_mgr.accept_check(grace_id, check_id)
        
        # Forward to someone else
        success, message, new_check_id = self.check_mgr.forward_check(
            user_id=grace_id,
            check_id=check_id,
            new_payee_name="Hannah"
        )
        
        self.assert_true(success, "Check forwarded successfully")
        self.assert_not_none(new_check_id, "New check created")
        self.assert_true(new_check_id != check_id, "New check has different ID")
        
        # Verify original check is FORWARDED
        cursor.execute("SELECT status FROM checks WHERE id = ?", (check_id,))
        status = cursor.fetchone()['status']
        self.assert_equal(status, 'FORWARDED', "Original check marked FORWARDED")
        
        # Verify new check exists and is PENDING
        cursor.execute("SELECT * FROM checks WHERE id = ?", (new_check_id,))
        new_check = cursor.fetchone()
        self.assert_equal(new_check['status'], 'PENDING', "New check is PENDING")
        self.assert_equal(new_check['amount'], 1000.0, "Amount preserved")
    
    def test_forward_check_not_accepted(self):
        """Test that only ACCEPTED checks can be forwarded"""
        print("\n➡️  Test: Forward Check (Not Accepted)")
        
        # Issue check (but don't accept)
        success, _, check_id = self.check_mgr.issue_check(1, "Ivan", 500.0)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'Ivan'")
        ivan_id = cursor.fetchone()['id']
        
        # Try to forward without accepting
        success, message, _ = self.check_mgr.forward_check(
            user_id=ivan_id,
            check_id=check_id,
            new_payee_name="Jack"
        )
        
        self.assert_true(not success, "Cannot forward non-accepted check")
        self.assert_true("not found" in message.lower() or "not accepted" in message.lower(),
                        "Appropriate error message")
    
    def test_get_user_checks(self):
        """Test retrieving user checks"""
        print("\n📋 Test: Get User Checks")
        
        # Issue multiple checks
        self.check_mgr.issue_check(1, "Alice", 100.0)
        self.check_mgr.issue_check(1, "Bob", 200.0)
        self.check_mgr.issue_check(2, "TestUser1", 300.0)  # Incoming for User1
        
        # Get all checks for User1
        checks = self.check_mgr.get_user_checks(1, 'all')
        
        self.assert_true(len(checks) >= 3, f"At least 3 checks returned (got {len(checks)})")
        
        # Test filtering
        outgoing = self.check_mgr.get_user_checks(1, 'outgoing')
        self.assert_true(len(outgoing) >= 2, "Outgoing checks filtered")
        
        incoming = self.check_mgr.get_user_checks(1, 'incoming')
        self.assert_true(len(incoming) >= 1, "Incoming checks filtered")
    
    def test_get_user_balance(self):
        """Test retrieving user balance"""
        print("\n💵 Test: Get User Balance")
        
        balance = self.check_mgr.get_user_balance(1)
        
        self.assert_equal(balance, 10000.0, "Correct balance retrieved")
        
        # Test non-existent user
        balance_none = self.check_mgr.get_user_balance(999)
        self.assert_true(balance_none is None, "None returned for non-existent user")
    
    def test_entity_integration(self):
        """Test integration with EntityManager"""
        print("\n🏢 Test: Entity Integration")
        
        # Issue check creates entity
        self.check_mgr.issue_check(1, "EntityTest", 500.0)
        
        # Verify entity was created
        entities = self.entity_mgr.list_entities()
        entity_names = [e['name'] for e in entities]
        
        self.assert_true("EntityTest" in entity_names, "Entity created via check issuance")
        
        # Check entity stats
        entity = [e for e in entities if e['name'] == 'EntityTest'][0]
        self.assert_true(entity['total_transactions'] > 0, "Transaction count updated")
        self.assert_true(entity['total_volume'] >= 500.0, "Volume tracked")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("🧪 CHECK MANAGER TEST SUITE")
        print("="*70)
        
        self.test_issue_check_success()
        self.test_issue_check_invalid_issuer()
        self.test_issue_check_creates_payee()
        self.test_accept_check_by_id()
        self.test_accept_check_by_issuer_name()
        self.test_accept_check_not_pending()
        self.test_deny_check_by_id()
        self.test_deny_check_by_issuer_name()
        self.test_forward_check()
        self.test_forward_check_not_accepted()
        self.test_get_user_checks()
        self.test_get_user_balance()
        self.test_entity_integration()
        
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
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {self.failed} test(s) need attention")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestCheckManager()
    try:
        success = tester.run_all_tests()
        tester.cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        tester.cleanup()
        sys.exit(1)
