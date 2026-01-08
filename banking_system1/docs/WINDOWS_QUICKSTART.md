# ⚡ QUICK START - Windows

## 🎯 Three Commands to Test Everything

### 1️⃣ Test Intent Parser
```cmd
cd C:\Users\georg\chuck\banking_system1
python tests\quick_test.py
```

**Should see:**
```
✅ 'Issue check to Alice for $500' -> ISSUE_CHECK
✅ 'Accept check from Bob' -> ACCEPT_CHECK
✅ 'Deny check #123' -> DENY_CHECK
✅ 'Forward check #456 to Charlie' -> FORWARD_CHECK
✅ 'What's my balance?' -> QUERY_BALANCE
✅ 'Show my checks' -> QUERY_CHECKS

🎉 All tests passed!
```

---

### 2️⃣ Create Some Data
```cmd
python chat.py
```

**Type these commands:**
```
Issue check to Alice for $500
Issue check to Bob for $750  
Issue check to Charlie for $300
Show my checks
quit
```

---

### 3️⃣ View the Database
```cmd
python view_database.py
```

**You'll see:**
- All users
- All checks with maturity dates
- Entity reputation scores
- Transaction history with confidence scores
- Statistics and patterns

---

## 📊 Specific Views

```cmd
# Just check status
python view_database.py --checks

# Just transaction history
python view_database.py --history

# Just statistics
python view_database.py --stats

# Overview only
python view_database.py --overview

# Entities (counterparties)
python view_database.py --entities
```

---

## ❌ If Something Goes Wrong

### Error: `No module named 'intent_parser'`
**Fix**: Make sure you're in the project root:
```cmd
cd C:\Users\georg\chuck\banking_system1
```

### Error: `Database file not found`
**Fix**: Create data first:
```cmd
python chat.py
```
Type a few commands, then `quit`.

### Error: `No module named 'managers'`
**Fix**: Use the simple quick test instead:
```cmd
python tests\quick_test.py
```

---

## ✅ That's It!

Three commands:
1. `python tests\quick_test.py` - Test the system
2. `python chat.py` - Create data
3. `python view_database.py` - See what's stored

**Everything works! 🎉**
