# 🧪 Testing Guide for Windows

## ⚠️ Important: Your Project Structure

Your project has a **flat structure** (all files in one directory):
```
banking_system1/
├── intent_parser.py
├── check_manager.py
├── transaction_manager.py
├── conversation_agent.py
├── schema.py
├── config.py
├── chat.py
├── web_app.py
└── tests/
    └── quick_test.py
```

NOT the hierarchical structure:
```
❌ managers/intent_parser.py    (This doesn't exist in your project)
❌ database/schema.py            (This doesn't exist either)
```

---

## ✅ Quick Test (Works Immediately)

**Step 1**: Open Command Prompt in your project directory
```cmd
cd C:\Users\georg\chuck\banking_system1
```

**Step 2**: Run the quick test
```cmd
python tests\quick_test.py
```

**Expected Output:**
```
🧪 QUICK INTENT PARSER TEST
======================================================================
✅ 'Issue check to Alice for $500' -> ISSUE_CHECK
✅ 'Accept check from Bob' -> ACCEPT_CHECK
✅ 'Deny check #123' -> DENY_CHECK
✅ 'Forward check #456 to Charlie' -> FORWARD_CHECK
✅ 'What's my balance?' -> QUERY_BALANCE
✅ 'Show my checks' -> QUERY_CHECKS

Results: 6 passed, 0 failed
🎉 All tests passed!
```

---

## 🗄️ View Your Database

**Step 1**: First, create a database by running the system
```cmd
python chat.py
```

Type a few commands like:
- `Issue check to Alice for $500`
- `Issue check to Bob for $300`
- `quit`

**Step 2**: View the database
```cmd
python view_database.py
```

OR view specific sections:
```cmd
python view_database.py --checks
python view_database.py --users
python view_database.py --entities
python view_database.py --stats
```

---

## 📊 What You'll See

### Database Overview
```
📊 DATABASE OVERVIEW
======================================================================
Database: banking_system.db
Tables: 7

Table Counts:
  📋 checks........................     5 rows
  📋 entities......................     3 rows
  📋 users.........................     2 rows
  📋 transaction_history...........    10 rows
```

### Check Details
```
📝 CHECKS
======================================================================

PENDING (3 checks):
  Check #1: $500.00
    From: DemoUser → To: Alice
    Issued: 2026-01-07 15:30:42
    Maturity: 2026-01-07 15:30  ← Immediate maturity (0 days default)

  Check #2: $300.00
    From: DemoUser → To: Bob
    Issued: 2026-01-07 15:31:15
    Maturity: 2026-01-07 15:31
```

### Transaction History
```
📜 TRANSACTION HISTORY
======================================================================

[2026-01-07 15:30:42]
  User: DemoUser
  Operation: ISSUE_CHECK
  Counterparty: Alice
  Amount: $500.00
  Status: SUCCESS
  Confidence: 70%
  Input: "Issue check to Alice for $500"
```

### Statistics
```
📈 STATISTICS
======================================================================

Check Statistics by Status:
  PENDING.............     3 checks | Total: $1,300.00 | Avg: $433.33
  ACCEPTED............     2 checks | Total:   $800.00 | Avg: $400.00

Operation Statistics:
  ISSUE_CHECK.........     5 ops | Success: 100.0% | Confidence: 70.0%
  ACCEPT_CHECK........     2 ops | Success: 100.0% | Confidence: 75.0%

Entity Statistics:
  Total Entities: 3
  Avg Transactions per Entity: 2.3
  Avg Volume per Entity: $543.33
  Avg Reputation Score: 50.0/100
```

---

## 🎯 Testing Checklist

✅ **Quick Test** (Verifies intent parser works)
```cmd
python tests\quick_test.py
```

✅ **Database Viewer** (Shows all data)
```cmd
python view_database.py
```

✅ **Manual Testing** (Interactive)
```cmd
python chat.py
```

---

## 🔍 Understanding Your System

### What Gets Stored in the Database

**1. Users** - Account information
- Username
- Balance (informational, not enforced for postdated checks)
- Creation date

**2. Checks** - All check operations
- Issuer → Payee relationship
- Amount
- Status (PENDING, ACCEPTED, DENIED, FORWARDED)
- **Maturity date** ← Key feature for postdated checks
- Issue timestamp

**3. Entities** - Counterparty tracking (for behavioral analysis!)
- Name
- Entity type (USER, MERCHANT, BANK)
- Total transactions with this party
- Total volume
- **Reputation score** (0-100)
- Last interaction timestamp

**4. Transaction History** - Complete audit trail
- User who performed operation
- Operation type
- Counterparty involved
- Amount
- Success/failure status
- **Conversation context** (exact user input)
- **Intent confidence** (NLP confidence score 0-100%)
- Timestamp

---

## 🧠 For Your Research

The database captures **behavioral finance signals**:

### 1. **Intent Confidence** (Behavioral Clarity Metric)
```sql
SELECT AVG(intent_confidence), operation_type 
FROM transaction_history 
GROUP BY operation_type
```
→ "Do clearer commands correlate with better outcomes?"

### 2. **Entity Reputation** (Trust Network)
```sql
SELECT name, reputation_score, total_transactions, total_volume 
FROM entities 
ORDER BY reputation_score DESC
```
→ "Do high-reputation counterparties get different treatment?"

### 3. **Maturity Patterns** (Time Preferences)
```sql
SELECT 
  JULIANDAY(maturity_date) - JULIANDAY(issued_at) as days_to_maturity,
  amount,
  status
FROM checks
```
→ "How do users discount future payments?"

### 4. **Linguistic Patterns** (NLP Analysis)
```sql
SELECT conversation_context, intent_confidence, status 
FROM transaction_history
WHERE operation_type = 'ISSUE_CHECK'
```
→ "What phrases predict successful transactions?"

---

## ❌ Troubleshooting

### Error: "No module named 'managers'"
**Cause**: Tests are looking for subdirectories that don't exist in your flat structure.

**Solution**: Use the quick test instead:
```cmd
python tests\quick_test.py
```

### Error: "Database file not found"
**Cause**: No database exists yet.

**Solution**: Create one first:
```cmd
python chat.py
```
Then type a few commands and quit. Now try:
```cmd
python view_database.py
```

### Error: "Import Error"
**Cause**: Not in project root directory.

**Solution**: Navigate to project root:
```cmd
cd C:\Users\georg\chuck\banking_system1
python tests\quick_test.py
```

---

## 🎓 Testing Best Practices

### 1. Test After Changes
```cmd
# Made a change to intent_parser.py?
python tests\quick_test.py
```

### 2. Inspect Database Regularly
```cmd
# After each test session
python view_database.py --stats
```

### 3. Monitor Entity Growth
```cmd
python view_database.py --entities
```
Useful for seeing how counterparty network evolves!

### 4. Check Transaction Confidence
```cmd
python view_database.py --history
```
Look for patterns in confidence scores.

---

## 📦 Files Included

- ✅ **tests/quick_test.py** - Simple intent parser verification
- ✅ **view_database.py** - Comprehensive database inspector
- ✅ **TEST_README_WINDOWS.md** - This file

---

## 🚀 Quick Start Commands

```cmd
# 1. Navigate to project
cd C:\Users\georg\chuck\banking_system1

# 2. Test intent parser
python tests\quick_test.py

# 3. Use the system
python chat.py

# 4. View what was stored
python view_database.py

# 5. See statistics
python view_database.py --stats
```

---

## 💡 Pro Tips

### Tip 1: Database is SQLite
You can also view it with any SQLite viewer:
- [DB Browser for SQLite](https://sqlitebrowser.org/) (Free, GUI)
- [DBeaver](https://dbeaver.io/) (Free, professional)

File location: `banking_system.db` in your project folder

### Tip 2: Export Data for Analysis
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('banking_system.db')
df = pd.read_sql_query("SELECT * FROM transaction_history", conn)
df.to_csv('transactions.csv', index=False)
```

### Tip 3: Custom Queries
```python
import sqlite3

conn = sqlite3.connect('banking_system.db')
cursor = conn.cursor()

# Your research queries here
cursor.execute("""
    SELECT 
        AVG(intent_confidence) as avg_confidence,
        status,
        COUNT(*) as count
    FROM transaction_history
    GROUP BY status
""")

for row in cursor.fetchall():
    print(row)
```

---

## ✅ You're Ready!

**Working features:**
- ✅ Intent parser (natural language → structured data)
- ✅ Database viewer (inspect all stored data)
- ✅ Quick tests (verify system health)

**Next steps:**
1. Run `python tests\quick_test.py` to verify
2. Use `python chat.py` to create some data
3. Run `python view_database.py` to see what was stored
4. Start exploring the behavioral finance signals! 📊

---

**Questions? Check the main documentation or just experiment!** 🎉
