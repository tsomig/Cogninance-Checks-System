#!/usr/bin/env python3
"""
Unit Tests for IntentParser
===========================

Tests natural language parsing for all banking operations.
"""

import sys
import os
from datetime import datetime

# Add test environment to path
sys.path.insert(0, '/home/claude/test_env')

from managers.intent_parser import IntentParser


class TestIntentParser:
    """Test suite for IntentParser"""
    
    def __init__(self):
        self.parser = IntentParser()
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
    
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
    
    def assert_greater_equal(self, actual, threshold, test_name):
        """Assert greater than or equal"""
        self.tests_run += 1
        if actual >= threshold:
            self.passed += 1
            print(f"  ✅ {test_name} ({actual:.0%} >= {threshold:.0%})")
            return True
        else:
            self.failed += 1
            print(f"  ❌ {test_name} ({actual:.0%} < {threshold:.0%})")
            return False
    
    def test_issue_check_basic(self):
        """Test basic check issuance parsing"""
        print("\n📝 Test: Issue Check (Basic)")
        
        intent = self.parser.parse("Issue a check to Alice for $500")
        
        self.assert_equal(intent.operation, "ISSUE_CHECK", "Operation identified")
        self.assert_equal(intent.parameters.get('counterparty'), 'Alice', "Counterparty extracted")
        self.assert_equal(intent.parameters.get('amount'), 500.0, "Amount extracted")
        self.assert_greater_equal(intent.confidence, 0.5, "Confidence threshold met")
    
    def test_issue_check_variations(self):
        """Test various phrasings for issuing checks"""
        print("\n📝 Test: Issue Check (Variations)")
        
        test_cases = [
            ("Write a check for Bob $1000", "Bob", 1000.0),
            ("Send $250 to Charlie", "Charlie", 250.0),
            ("Pay Alice $750", "Alice", 750.0),
            ("Create check to David for $1500", "David", 1500.0)
        ]
        
        for phrase, expected_payee, expected_amount in test_cases:
            intent = self.parser.parse(phrase)
            self.assert_equal(intent.operation, "ISSUE_CHECK", f"'{phrase}' -> ISSUE_CHECK")
            self.assert_equal(intent.parameters.get('counterparty'), expected_payee, f"Payee: {expected_payee}")
            self.assert_equal(intent.parameters.get('amount'), expected_amount, f"Amount: ${expected_amount}")
    
    def test_issue_check_with_date(self):
        """Test check issuance with maturity dates"""
        print("\n📝 Test: Issue Check (With Dates)")
        
        test_cases = [
            "Issue check to Alice for $500 due Jan 15",
            "Write check for Bob $1000 maturity date February 1st 2026",
            "Send $250 to Charlie on March 10th"
        ]
        
        for phrase in test_cases:
            intent = self.parser.parse(phrase)
            self.assert_equal(intent.operation, "ISSUE_CHECK", f"'{phrase}' parsed")
            self.assert_true('custom_date' in intent.parameters or 'amount' in intent.parameters, 
                           f"Date or amount extracted from '{phrase}'")
    
    def test_accept_check(self):
        """Test check acceptance parsing"""
        print("\n📝 Test: Accept Check")
        
        # By counterparty name
        intent1 = self.parser.parse("Accept check from Alice")
        self.assert_equal(intent1.operation, "ACCEPT_CHECK", "Operation: ACCEPT_CHECK")
        self.assert_equal(intent1.parameters.get('counterparty'), 'Alice', "Counterparty extracted")
        
        # By check number
        intent2 = self.parser.parse("Accept check #123")
        self.assert_equal(intent2.operation, "ACCEPT_CHECK", "Operation: ACCEPT_CHECK")
        self.assert_equal(intent2.parameters.get('check_id'), 123, "Check ID extracted")
        
        # Variations
        intent3 = self.parser.parse("Approve the check from Bob")
        self.assert_equal(intent3.operation, "ACCEPT_CHECK", "Variation: 'approve' recognized")
    
    def test_deny_check(self):
        """Test check denial parsing"""
        print("\n📝 Test: Deny Check")
        
        # By counterparty name
        intent1 = self.parser.parse("Deny check from Charlie")
        self.assert_equal(intent1.operation, "DENY_CHECK", "Operation: DENY_CHECK")
        self.assert_equal(intent1.parameters.get('counterparty'), 'Charlie', "Counterparty extracted")
        
        # By check number
        intent2 = self.parser.parse("Reject check #456")
        self.assert_equal(intent2.operation, "DENY_CHECK", "Operation: DENY_CHECK")
        self.assert_equal(intent2.parameters.get('check_id'), 456, "Check ID extracted")
        
        # Variations
        intent3 = self.parser.parse("Decline the check from David")
        self.assert_equal(intent3.operation, "DENY_CHECK", "Variation: 'decline' recognized")
    
    def test_forward_check(self):
        """Test check forwarding parsing"""
        print("\n📝 Test: Forward Check")
        
        intent = self.parser.parse("Forward check #123 to Alice")
        
        self.assert_equal(intent.operation, "FORWARD_CHECK", "Operation: FORWARD_CHECK")
        self.assert_equal(intent.parameters.get('check_id'), 123, "Check ID extracted")
        self.assert_equal(intent.parameters.get('to_counterparty'), 'Alice', "Recipient extracted")
    
    def test_query_balance(self):
        """Test balance query parsing"""
        print("\n📝 Test: Query Balance")
        
        test_cases = [
            "What's my balance?",
            "Show balance",
            "How much money do I have?",
            "Check my funds"
        ]
        
        for phrase in test_cases:
            intent = self.parser.parse(phrase)
            self.assert_equal(intent.operation, "QUERY_BALANCE", f"'{phrase}' -> QUERY_BALANCE")
    
    def test_query_checks(self):
        """Test check query parsing"""
        print("\n📝 Test: Query Checks")
        
        test_cases = [
            "Show my checks",
            "List all checks",
            "Display my pending checks",
            "View my issued checks",
            "What's the total of my checks"  # New test for total/sum
        ]
        
        for phrase in test_cases:
            intent = self.parser.parse(phrase)
            self.assert_equal(intent.operation, "QUERY_CHECKS", f"'{phrase}' -> QUERY_CHECKS")
    
    def test_query_history(self):
        """Test transaction history query"""
        print("\n📝 Test: Query History")
        
        test_cases = [
            "Show my transaction history",
            "View recent activity",
            "List my transactions"
        ]
        
        for phrase in test_cases:
            intent = self.parser.parse(phrase)
            self.assert_equal(intent.operation, "QUERY_HISTORY", f"'{phrase}' -> QUERY_HISTORY")
    
    def test_layer2_operations(self):
        """Test Layer 2 (tokenization) operation recognition"""
        print("\n📝 Test: Layer 2 Operations")
        
        # Tokenize
        intent1 = self.parser.parse("Tokenize check #789")
        self.assert_equal(intent1.operation, "TOKENIZE_CHECK", "Tokenize recognized")
        self.assert_equal(intent1.parameters.get('check_id'), 789, "Check ID extracted")
        
        # Buy token
        intent2 = self.parser.parse("Buy token #101")
        self.assert_equal(intent2.operation, "BUY_TOKEN", "Buy token recognized")
        self.assert_equal(intent2.parameters.get('token_id'), 101, "Token ID extracted")
        
        # Redeem token
        intent3 = self.parser.parse("Redeem token #202")
        self.assert_equal(intent3.operation, "REDEEM_TOKEN", "Redeem recognized")
        self.assert_equal(intent3.parameters.get('token_id'), 202, "Token ID extracted")
    
    def test_ambiguous_inputs(self):
        """Test handling of ambiguous inputs"""
        print("\n📝 Test: Ambiguous Inputs")
        
        # Missing amount
        intent1 = self.parser.parse("Issue check to Alice")
        self.assert_true(intent1.needs_clarification(), "Missing amount flagged")
        
        # Missing payee
        intent2 = self.parser.parse("Issue check for $500")
        self.assert_true(intent2.needs_clarification(), "Missing payee flagged")
        
        # Unclear command
        intent3 = self.parser.parse("Do something with checks")
        self.assert_true(intent3.confidence < 0.5, "Low confidence for unclear input")
    
    def test_confidence_scoring(self):
        """Test confidence scoring accuracy"""
        print("\n📝 Test: Confidence Scoring")
        
        # High confidence (clear command)
        intent1 = self.parser.parse("Issue check to Alice for $500")
        self.assert_greater_equal(intent1.confidence, 0.6, "High confidence for clear command")
        
        # Medium confidence (somewhat clear)
        intent2 = self.parser.parse("Pay Alice $500")
        self.assert_greater_equal(intent2.confidence, 0.4, "Medium confidence maintained")
        
        # Low confidence (very unclear)
        intent3 = self.parser.parse("What about that thing?")
        self.assert_true(intent3.confidence < 0.3, "Low confidence for unclear input")
    
    def test_edge_cases(self):
        """Test edge cases and unusual inputs"""
        print("\n📝 Test: Edge Cases")
        
        # Empty string
        intent1 = self.parser.parse("")
        self.assert_equal(intent1.operation, "UNKNOWN", "Empty input handled")
        
        # Very long name
        intent2 = self.parser.parse("Issue check to Alice Jane Marie Smith for $100")
        self.assert_equal(intent2.operation, "ISSUE_CHECK", "Long name handled")
        
        # Large amount
        intent3 = self.parser.parse("Issue check to Alice for $1000000")
        self.assert_equal(intent3.parameters.get('amount'), 1000000.0, "Large amount handled")
        
        # Decimal amounts
        intent4 = self.parser.parse("Issue check to Bob for $99.99")
        self.assert_equal(intent4.parameters.get('amount'), 99.99, "Decimal amount handled")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("🧪 INTENT PARSER TEST SUITE")
        print("="*70)
        
        self.test_issue_check_basic()
        self.test_issue_check_variations()
        self.test_issue_check_with_date()
        self.test_accept_check()
        self.test_deny_check()
        self.test_forward_check()
        self.test_query_balance()
        self.test_query_checks()
        self.test_query_history()
        self.test_layer2_operations()
        self.test_ambiguous_inputs()
        self.test_confidence_scoring()
        self.test_edge_cases()
        
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
    tester = TestIntentParser()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
