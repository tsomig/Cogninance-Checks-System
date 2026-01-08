# QUICKSTART GUIDE

## 🚀 Get Started in 2 Minutes

### Step 1: Test IntentParser
```bash
cd banking_system/managers
python intent_parser.py
```

You should see output like:
```
✓ "Issue check to Alice for $500"     → 70% confidence
✓ "Write check for Bob $1000"         → 70% confidence
```

### Step 2: Initialize Database
```bash
cd ../database
python schema.py
```

You should see:
```
✓ Database schema initialized successfully
✓ 7 tables created
✓ EntityManager working
✓ TransactionLogger working
```

### Step 3: Run Integration Demo
```bash
cd ..
python integration_demo.py
```

This will:
- Process 7 sample commands
- Show entity resolution
- Log all transactions
- Display summary statistics
- Create `demo_banking.db` file

### Step 4: Inspect the Database

```bash
# Option 1: Python
python3
>>> import sqlite3
>>> conn = sqlite3.connect('demo_banking.db')
>>> cursor = conn.cursor()
>>> cursor.execute("SELECT * FROM entities")
>>> cursor.fetchall()

# Option 2: SQLite CLI
sqlite3 demo_banking.db
> SELECT * FROM entities;
> SELECT * FROM transaction_history;
```

## 📝 Quick Usage Example

```python
# Import components
from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser

# Initialize
db = DatabaseManager("my_banking.db")
db.connect()
db.initialize_schema()

parser = IntentParser()
entity_mgr = EntityManager(db)
logger = TransactionLogger(db)

# Process user input
user_input = "Issue a check to Alice for $500"
intent = parser.parse(user_input)

if intent.is_confident():
    # Resolve entity
    entity_id = entity_mgr.get_or_create_entity(
        intent.parameters['counterparty']
    )
    
    # Log transaction
    logger.log_transaction(
        user_id=1,
        operation_type=intent.operation,
        status='SUCCESS',
        counterparty_id=entity_id,
        amount=intent.parameters['amount'],
        conversation_context=user_input,
        intent_confidence=intent.confidence
    )
    
    print(f"✓ {intent.operation} executed successfully")
else:
    print(f"⚠️ Needs clarification: {intent.ambiguities}")

db.close()
```

## 🔧 Troubleshooting

**Import errors?**
- Make sure you're in the correct directory
- Python 3.7+ required
- No external dependencies needed

**Database locked?**
- Close any open SQLite connections
- Delete `*.db` files and re-run

**Low confidence scores?**
- Check your input matches expected patterns
- See `docs/INTENT_PARSER_DOCS.md` for examples

## 📚 Next Steps

1. Read `README.md` for full architecture overview
2. Check `docs/INTENT_PARSER_DOCS.md` for NLP details
3. Integrate with your existing CheckManager
4. Add Claude API conversational layer

## ✅ What's Working

- ✅ IntentParser: Natural language → structured operations
- ✅ Database: Extended schema with entities + history
- ✅ EntityManager: Counterparty resolution
- ✅ TransactionLogger: Complete audit trail
- ✅ Integration: All components work together

## 🔜 What's Next

Build the orchestration layer:
- TransactionManager: Connect parser → managers → logger
- ConversationAgent: Claude API integration
- Web interface: Chat UI
