"""
Intent Parser - Complete Logic
==============================
FIXED: 
1. Supports "Check FOR $X TO [Name]" structure.
2. Flexible Date Parsing (Handles 12-12-2028, Dec 12, etc.).
3. Boosted Confidence to prevent unnecessary "Clarification" questions.
"""
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Intent:
    operation: str
    confidence: float
    parameters: Dict[str, Any]
    raw_text: str
    ambiguities: List[str]
    timestamp: datetime = None
    def __post_init__(self): self.timestamp = datetime.now()
    def is_confident(self): return self.confidence >= 0.5
    def needs_clarification(self): return bool(self.ambiguities) or self.confidence < 0.4

class IntentParser:
    def __init__(self):
        self._init_vocabulary()
        self._init_patterns()
        self._init_extractors()
    
    def _init_vocabulary(self):
        self.hot_words = {
            'ISSUE_CHECK': {'primary': ['issue', 'write', 'create', 'pay'], 'secondary': ['check'], 'context': ['to', 'for']},
            'ACCEPT_CHECK': {'primary': ['accept'], 'secondary': ['check'], 'context': ['#']},
            'DENY_CHECK': {'primary': ['deny', 'reject'], 'secondary': ['check'], 'context': ['#']},
            'FORWARD_CHECK': {'primary': ['forward'], 'secondary': ['check'], 'context': ['to']},
            'REVOKE_OP': {'primary': ['cancel', 'revoke', 'undo'], 'secondary': ['check', 'forward'], 'context': ['#']},
            'QUERY_CHECKS': {'primary': ['show', 'list'], 'secondary': ['checks'], 'context': []}
        }

    def _init_patterns(self):
        amt = r'\$?(\d+(?:[.,]\d+)?)'
        name = r"([A-Za-z0-9_'.&-]+(?:\s+[A-Za-z0-9_'.&-]+)*)"
        
        self.patterns = {
            'ISSUE_CHECK': [
                # 1. Standard: "Check TO Bob FOR $200"
                fr'(?:issue|write|create|pay)\s+(?:a\s+)?check\s+to\s+{name}\s+for\s+{amt}',
                # 2. Reversed: "Check OF $200 TO Bob"
                fr'(?:issue|write|create|pay)\s+(?:a\s+)?check\s+of\s+{amt}\s+to\s+{name}',
                # 3. Flexible: "Check FOR $200 TO Bob" (This was missing!)
                fr'(?:issue|write|create|pay)\s+(?:a\s+)?check\s+(?:for|of)\s+{amt}\s+to\s+{name}',
                # 4. Short: "Pay Bob $200"
                fr'pay\s+{name}\s+{amt}'
            ],
            'FORWARD_CHECK': [fr'forward\s+(?:check\s+)?(?:number\s+|#)?(\d+)\s+to\s+{name}'],
            'REVOKE_OP': [r'(?:cancel|revoke|undo)\s+.*?(?:number\s+|#)?(\d+)'],
            'ACCEPT_CHECK': [r'accept\s+.*?(?:#)?(\d+)'],
            'DENY_CHECK': [r'deny\s+.*?(?:#)?(\d+)']
        }

    def _init_extractors(self):
        self.entity_patterns = {'amount': [r'\$?(\d+(?:[.,]\d+)?)']}

    def parse(self, user_input: str) -> Intent:
        norm = re.sub(r'\s+', ' ', user_input.lower().strip())
        scores = self._score(norm)
        if not scores: return Intent('UNKNOWN', 0.0, {}, user_input, [])
        op = max(scores, key=scores.get)
        params, conf = self._extract(user_input, op)
        return Intent(op, (scores[op]+conf)/2, params, user_input, [])

    def _score(self, text):
        scores = {}
        for op, kw in self.hot_words.items():
            s = sum(1 for w in kw['primary'] if w in text)*0.4 + sum(1 for w in kw['secondary'] if w in text)*0.3
            if s > 0.2: scores[op] = min(s, 1.0)
        return scores

    def _extract(self, text, op):
        params = {}
        conf = 0.0
        
        # --- 1. BATCH DETECTION (Must be first) ---
        list_match = re.search(r'(?:checks?|#)\s*([0-9]+(?:(?:[\s,]|and)+[0-9]+)+)', text, re.IGNORECASE)
        if list_match:
            raw_nums = re.findall(r'\d+', list_match.group(1))
            params['check_ids'] = list(set([int(x) for x in raw_nums]))

        # --- 2. SINGLE CHECK / MAIN PATTERNS ---
        if op in self.patterns:
            for pat in self.patterns[op]:
                if match := re.search(pat, text, re.IGNORECASE):
                    groups = match.groups()
                    if op == 'ISSUE_CHECK':
                        g1, g2 = groups[0], groups[1]
                        
                        # Helper to identify which group is the amount
                        is_number = re.match(r'^[\d.,]+$', g1.strip())
                        if is_number:
                            params['amount'] = float(g1.replace(',',''))
                            params['counterparty'] = g2.strip()
                        else:
                            params['counterparty'] = g1.strip()
                            params['amount'] = float(g2.replace(',',''))
                            
                    elif op == 'FORWARD_CHECK':
                        params['check_id']=int(groups[0])
                        params['to_counterparty']=groups[1].strip()
                    
                    elif op in ['REVOKE_OP', 'ACCEPT_CHECK', 'DENY_CHECK']:
                        if 'check_ids' not in params:
                            params['check_id']=int(groups[0])
                    
                    # FIX: High confidence (0.8) stops "Needs Clarification"
                    conf = 0.8; break
        
        # --- 3. FALLBACKS ---
        if 'check_ids' not in params and 'check_id' not in params:
             ids = re.findall(r'(?:check\s+|#)\s*(\d+)', text, re.IGNORECASE)
             if ids: params['check_ids'] = list(set([int(x) for x in ids]))

        for p in self.entity_patterns['amount']:
            if 'amount' not in params and (m := re.search(p, text)): 
                params['amount'] = float(m.group(1).replace(',',''))
        
        # FIX: Flexible Date Parsing (Handles multiple formats)
        if m := re.search(r'(?:on|due|date)\s+([A-Za-z0-9\s,-]+)', text, re.IGNORECASE):
             date_str = m.group(1).strip()
             # Try multiple formats
             for fmt in ["%Y-%m-%d", "%m-%d-%Y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"]:
                 try:
                     params['custom_date'] = datetime.strptime(date_str, fmt)
                     break
                 except ValueError:
                     continue
             
        if op == 'ACCEPT_CHECK' and 'all' in text.lower(): params['accept_all'] = True
        return params, conf