# Conversational AI Banking System - Enhanced MVP

## 🎯 Overview

A two-layer conversational banking system that bridges traditional check management with financial tokenization through natural language interactions.

### Core Innovation
- **Layer 1**: Traditional check operations (issue, accept, deny, forward)
- **Layer 2**: Check tokenization for instant liquidity
- **Natural Language Interface**: All operations via conversation with Claude API

### New Enhancements
- **IntentParser**: Hot words dictionary for NLP → operation mapping
- **Transaction History**: Complete audit trail for behavioral finance analysis
- **Entity Management**: Counterparty database with reputation tracking

---

## 📁 Project Structure

```
banking_system/
├── __init__.py
├── managers/
│   ├── __init__.py
│   └── intent_parser.py       # NLP hot words + pattern matching
├── database/
│   ├── __init__.py
│   └── schema.py              # Extended schema + EntityManager + TransactionLogger
├── models/
│   ├── __init__.py
│   └── (your existing models will go here)
├── tests/
│   ├── __init__.py
│   └── (test files)
└── docs/
    └── (documentation)

Root files:
├── banking_system.db          # SQLite database (created on first run)
├── INTENT_PARSER_DOCS.md     # IntentParser documentation
└── README.md                  # This file
```

---

## 🗄️ Database Schema

### Existing Tables (from your MVP)
- `users` - User accounts and balances
- `checks` - Check issuance and status
- `tokens` - Tokenized checks
- `marketplace_transactions` - Token trading history

### New Tables (extensions)
- **`entities`** - Counterparty management
  - name, entity_type, reputation_score
  - total_transactions, total_volume
  - Tracks all counterparties for check operations

- **`transaction_history`** - Complete audit trail
  - operation_type, status, timestamp
  - conversation_context, intent_confidence
  - Links to users, entities, checks, tokens
  - Enables behavioral finance analysis

---

## 🚀 Getting Started

### Installation

```bash
# No external dependencies required (uses Python stdlib)
# Only requirement: Python 3.7+

# Test the IntentParser
cd banking_system/managers
python intent_parser.py

# Initialize database schema
cd ../database
python schema.py
```

### Quick Start

```python
# 1. Initialize database
from banking_system.database.schema import DatabaseManager, EntityManager, TransactionLogger

db = DatabaseManager("banking_system.db")
db.connect()
db.initialize_schema()

# 2. Create entity manager
entity_mgr = EntityManager(db)
alice_id = entity_mgr.get_or_create_entity("Alice", "USER")

# 3. Parse user intent
from banking_system.managers.intent_parser import IntentParser

parser = IntentParser()
intent = parser.parse("I want to issue a check to Alice for $500")

print(f"Operation: {intent.operation}")        # ISSUE_CHECK
print(f"Confidence: {intent.confidence:.0%}")  # 70%
print(f"Parameters: {intent.parameters}")      # {'counterparty': 'alice', 'amount': 500.0}

# 4. Log transaction
logger = TransactionLogger(db)
logger.log_transaction(
    user_id=1,
    operation_type=intent.operation,
    status='SUCCESS',
    counterparty_id=alice_id,
    amount=intent.parameters['amount'],
    conversation_context=intent.raw_text,
    intent_confidence=intent.confidence
)

db.close()
```

---

## 🧠 IntentParser

### Supported Operations

#### Layer 1: Check Management
- `ISSUE_CHECK` - "Issue a check to Alice for $500"
- `ACCEPT_CHECK` - "Accept check from Bob"
- `DENY_CHECK` - "Reject check from Charlie"
- `FORWARD_CHECK` - "Forward check 123 to David"

#### Layer 2: Tokenization
- `TOKENIZE_CHECK` - "Tokenize check 456"
- `BUY_TOKEN` - "Buy token 789"
- `REDEEM_TOKEN` - "Redeem token 101"

#### Queries
- `QUERY_BALANCE` - "What's my balance?"
- `QUERY_CHECKS` - "Show my checks"
- `QUERY_TOKENS` - "List my tokens"
- `QUERY_HISTORY` - "View transaction history"

### How It Works

```
User Input: "Issue check to Alice for $500"
     ↓
Hot Words Match: ['issue', 'check', 'to', 'for']
     ↓
Pattern Extraction: counterparty='Alice', amount=500.0
     ↓
Confidence Score: 70%
     ↓
Intent Object: Ready to execute
```

### Confidence Levels
- **≥50%**: Confident - ready to execute
- **40-49%**: Borderline - may need validation
- **<40%**: Needs clarification

---

## 📊 Entity Management

### Entity Types
- `USER` - Individual users
- `MERCHANT` - Business entities
- `BANK` - Financial institutions
- `UNKNOWN` - Unclassified

### Reputation Scoring
- Scale: 0-100
- Default: 50
- Updated based on transaction patterns
- Enables behavioral finance analysis

---

## 📝 Transaction History

Every interaction is logged:
- User command (natural language)
- Intent confidence score
- Operation type
- Counterparty involved
- Success/failure status
- Timestamps

### Use Cases
- Audit trail
- Behavioral pattern analysis
- Fraud detection
- User experience optimization
- Regulatory compliance

---

## 🔗 Next Steps: Integration

### What's Ready
✅ IntentParser - Maps language to operations  
✅ Database schema - Extended with entities + history  
✅ EntityManager - Counterparty CRUD  
✅ TransactionLogger - Audit trail  

### What's Needed
🔄 **TransactionManager** - Orchestrator connecting:
   - IntentParser → Extract intent
   - EntityManager → Resolve counterparties
   - CheckManager (your existing code) → Execute L1 operations
   - TokenizationManager (your existing code) → Execute L2 operations
   - TransactionLogger → Record everything

🔄 **ConversationAgent** - Claude API integration:
   - Receives user input
   - Calls IntentParser
   - If confident → Execute via TransactionManager
   - If unclear → Ask clarification
   - Return natural language response

---

## 🧪 Testing

### Test IntentParser
```bash
cd banking_system/managers
python intent_parser.py
```

Expected output:
```
✓ "Issue check to Alice for $500"     → 70% confidence
✓ "Write check for Bob $1000"         → 70% confidence
✓ "Reject checks from Charlie"        → 70% confidence
✓ "Tokenize check 456"                → 70% confidence
```

### Test Database Schema
```bash
cd banking_system/database
python schema.py
```

Expected output:
```
✓ Database schema initialized
✓ 7 tables created
✓ EntityManager working
✓ TransactionLogger working
```

---

## 📚 Documentation

- `INTENT_PARSER_DOCS.md` - Detailed IntentParser guide
- Database schema comments - Inline documentation
- Code docstrings - API documentation

---

## 🏗️ Architecture Diagram

```
User Input (Natural Language)
         ↓
   IntentParser
    (hot words + patterns)
         ↓
   Intent Object
    (operation + parameters + confidence)
         ↓
   TransactionManager
    (orchestrator - to be built)
         ↓
    ┌───────────┬──────────────┬──────────────────┐
    ↓           ↓              ↓                  ↓
EntityMgr  CheckMgr    TokenizationMgr   TransactionLogger
(resolve)  (Layer 1)      (Layer 2)         (audit trail)
    ↓           ↓              ↓                  ↓
         Database (SQLite)
```

---

## 🎓 Design Philosophy

### MVP Principles
- **Rule-based NLP**: No training needed, fast, debuggable
- **Single database**: Atomic transactions, simple queries
- **Confidence-aware**: Knows when it doesn't know
- **Extensible**: Easy to add new operations
- **Audit-first**: Everything logged for analysis

### Behavioral Finance Focus
- Track conversation patterns
- Measure intent confidence over time
- Build entity reputation profiles
- Enable future ML/behavioral analysis

---

## 📦 Ready to Download

All core components are complete and tested:
1. IntentParser with hot words dictionary
2. Extended database schema
3. EntityManager for counterparties
4. TransactionLogger for audit trail
5. Comprehensive documentation

Next phase: Build TransactionManager to connect everything with your existing CheckManager and TokenizationManager.

---

## 📧 Notes

- Database file (`banking_system.db`) is created automatically on first run
- All operations use SQLite transactions for data integrity
- Entity names are normalized (Title Case)
- Foreign keys enforce referential integrity
- Indices optimize common queries

---

**Status**: Core MVP infrastructure complete ✅  
**Next**: Build orchestration layer connecting all components
