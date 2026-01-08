# 🚀 QUICKSTART - Get Running in 2 Minutes

## Step 1: Install (30 seconds)

```bash
cd banking_system
pip install -r requirements.txt
```

That's it! Only one dependency: `anthropic` (Claude API SDK)

---

## Step 2: Run Interactive Chat (10 seconds)

```bash
python chat.py
```

You'll see:
```
🏦  CONVERSATIONAL BANKING SYSTEM - LIVE DEMO
...
🤖 Assistant: Hi! I'm your banking assistant. How can I help you today?

💬 DemoUser: _
```

---

## Step 3: Try Commands (1 minute)

Type naturally:

```
What's my balance?
```

```
Issue a check to Alice for $500
```

```
Send $1000 to Bob
```

```
Show my checks
```

```
Can I tokenize a check?
```

---

## Alternative: Automated Demo

Want to see it in action first?

```bash
python demo.py
```

This runs through 8 scenarios automatically, showing:
- Natural language understanding
- Check operations
- Balance queries
- Transaction history
- Layer 2 awareness

---

## Quick Commands in Chat

### Banking Operations
- **Issue**: "Issue check to [name] for $[amount]"
- **Accept**: "Accept check from [name]" or "Accept check #[number]"
- **Deny**: "Deny check from [name]" or "Reject check #[number]"
- **Forward**: "Forward check #[number] to [name]"

### Queries
- **Balance**: "balance" or "What's my balance?"
- **Checks**: "checks" or "Show my checks"
- **Help**: "help"
- **Exit**: "quit" or "exit"

---

## What You'll Experience

### Natural Conversation
```
You: Hi, what can you do?
Assistant: Hello! I'm your banking assistant. I can help you:
• Issue checks to anyone
• Accept or deny incoming checks
• Forward checks to other people
• Check your balance
• View all your checks
• See your transaction history
What would you like to do?
```

### Intelligent Responses
```
You: Send money to Alice
Assistant: I'd be happy to help! How much would you like to send to Alice?
```

### Error Handling
```
You: Issue a check for $100,000
Assistant: I'm sorry, but you have insufficient funds. Your current 
balance is $10,000.00, but you're trying to issue a check for $100,000.00. 
Would you like to issue a check for a different amount?
```

---

## Configuration

Everything is pre-configured! But if you want to customize:

Edit `config.py`:
```python
ANTHROPIC_API_KEY = "your-key"  # Already set
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Latest model
DEFAULT_USER_BALANCE = 10000.0  # Starting balance
```

---

## Troubleshooting

### API Key Error?
- Check `config.py` has the correct key
- Key format: `sk-ant-api03-...`

### Module Not Found?
```bash
pip install anthropic
```

### Database Locked?
```bash
rm banking_system.db
python chat.py
```

---

## Next Steps

1. **Explore**: Try different phrasings, see how Claude understands
2. **Test**: Issue checks, accept them, forward them
3. **Experiment**: Ask about features, query your account
4. **Extend**: Add new operations in `check_manager.py`

---

## File Guide

### To Run
- `chat.py` - Interactive chat interface ⭐
- `demo.py` - Automated demonstration

### To Configure  
- `config.py` - Settings & API key

### To Understand
- `README_LIVE.md` - Complete documentation
- `docs/` - Detailed guides

### To Extend
- `managers/check_manager.py` - Add operations
- `managers/conversation_agent.py` - Modify AI behavior
- `managers/intent_parser.py` - Add hot words

---

## Performance

- **Parse time**: <1ms
- **API response**: ~1-2 seconds
- **Database**: Instant
- **Total**: ~2 seconds per interaction

---

## Cost

Claude API usage:
- ~500-1000 tokens per turn
- Estimated: <$0.01 per conversation
- Pricing: Pay-as-you-go

---

## Demo Highlights

The system demonstrates:
✅ Natural language understanding
✅ Context preservation across turns
✅ Intent parsing with confidence
✅ Entity resolution
✅ Transaction execution
✅ Complete audit trail
✅ Professional AI responses
✅ Layer 2 awareness

---

## What's Working

🟢 Issue checks with natural language
🟢 Accept/deny incoming checks
🟢 Forward checks to others
🟢 Balance and status queries
🟢 Transaction history
🟢 Multi-turn conversations
🟢 Error handling
🟢 Entity management

---

**You're ready! Run `python chat.py` and start banking with AI. 🎉**
