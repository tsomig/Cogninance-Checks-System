# IntentParser Module Documentation

## Overview
The IntentParser is the **attention mechanism** of your conversational banking system. It maps natural language expressions to specific banking operations using hot words, pattern matching, and confidence scoring.

## Architecture

### 1. Hot Words Dictionary
Maps domain-specific keywords to banking operations:
- **Primary keywords** (weight: 0.40) - Core action verbs
- **Secondary keywords** (weight: 0.30) - Domain confirmers
- **Context keywords** (weight: 0.10) - Supporting signals

### 2. Regex Patterns
Extracts structured entities:
- Counterparty names (e.g., "Alice", "Bob")
- Amounts (e.g., "$500", "1000")
- Check/Token IDs (e.g., "check 123", "token 789")

### 3. Confidence Scoring
Combines multiple signals:
- Hot word matches
- Pattern extraction success
- Bonus for hitting both primary + secondary keywords
- Final score: 0.0 to 1.0

## Supported Operations

### Layer 1: Check Management
- `ISSUE_CHECK` - Create/write a check
- `ACCEPT_CHECK` - Accept incoming check
- `DENY_CHECK` - Reject incoming check  
- `FORWARD_CHECK` - Forward accepted check to another party

### Layer 2: Tokenization
- `TOKENIZE_CHECK` - Convert check to token
- `BUY_TOKEN` - Purchase token from marketplace
- `REDEEM_TOKEN` - Cash in token

### Queries
- `QUERY_BALANCE` - Check account balance
- `QUERY_CHECKS` - View checks (incoming/outgoing)
- `QUERY_TOKENS` - View token holdings
- `QUERY_HISTORY` - View transaction history

## Usage Example

```python
from intent_parser import IntentParser

parser = IntentParser()

# Parse user input
user_input = "I want to issue a check to Alice for $500"
intent = parser.parse(user_input)

print(f"Operation: {intent.operation}")
print(f"Confidence: {intent.confidence:.2%}")
print(f"Parameters: {intent.parameters}")

# Check if ready to execute
if intent.is_confident():
    # Execute operation
    pass
elif intent.needs_clarification():
    # Ask user for clarification
    print(f"Ambiguities: {intent.ambiguities}")
```

## Intent Object Structure

```python
@dataclass
class Intent:
    operation: str           # e.g., 'ISSUE_CHECK'
    confidence: float        # 0.0 to 1.0
    parameters: Dict         # Extracted entities
    raw_text: str           # Original input
    ambiguities: List[str]  # Detected uncertainties
    timestamp: datetime     # When parsed
```

## Confidence Thresholds

- **≥ 0.50**: Confident - ready to execute
- **< 0.40**: Needs clarification
- **0.40-0.49**: Borderline - may need validation

## Test Results

```
✓ "Issue check to Alice for $500"     → 70% confidence
✓ "Write check for Bob $1000"         → 70% confidence  
✓ "Reject checks from Charlie"        → 70% confidence
✓ "Forward check 123 to David"        → 70% confidence
✓ "Tokenize check 456"                → 70% confidence
✓ "Accept check from Alice"           → 70% confidence
✓ "Buy token 789"                     → 65% confidence
✓ "Redeem token 101"                  → 65% confidence
⚠ "What's my balance?"                → 25% confidence
✓ "Show me all my checks"             → 50% confidence
```

## Extension Guidelines

### Adding New Operations
1. Define hot words in `_initialize_hot_words()`
2. Add regex patterns in `_initialize_patterns()`
3. Update parameter mapping in `_map_groups_to_params()`
4. Add required parameters in `_detect_ambiguities()`

### Tuning Confidence
- Adjust weights in `_score_intents()`
- Modify pattern confidence boost in `_extract_parameters()`
- Change thresholds in `is_confident()` and `needs_clarification()`

## Next Steps

The IntentParser needs to connect to:
1. **TransactionManager** - Executes operations and logs to history
2. **EntityManager** - Manages counterparty database
3. **ConversationAgent** - Interfaces with Claude API
4. **CheckManager** - Existing Layer 1 operations
5. **TokenizationManager** - Existing Layer 2 operations

## Design Philosophy

The IntentParser follows MVP principles:
- **Rule-based**: Fast, deterministic, debuggable
- **No training needed**: Works out-of-box
- **Extensible**: Easy to add new operations
- **Graceful degradation**: Handles ambiguity appropriately
- **Confidence-aware**: Knows when it doesn't know
