"""
Conversation Agent - Claude API Integration
===========================================

Provides natural conversational interface using Claude API.
Makes the banking system feel alive and responsive.
"""

import anthropic
import json
from datetime import datetime, date  # <--- Added imports
from typing import Dict, List, Optional
from managers.transaction_manager import TransactionManager
import config


class ConversationAgent:
    """
    Manages conversations with users through Claude API.
    """
    
    def __init__(self, transaction_manager: TransactionManager):
        self.tx_mgr = transaction_manager
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        self.conversations = {}
    
    def chat(self, user_id: int, user_message: str, username: str = "User") -> str:
        """Main chat interface."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Process through transaction manager
        result = self.tx_mgr.process_command(user_id, user_message)
        
        # Build context for Claude
        context = self._build_context(user_id, user_message, result, username)
        
        # Get Claude's response
        response = self._call_claude(user_id, user_message, context)
        
        # Update history
        self.conversations[user_id].append({'role': 'user', 'content': user_message})
        self.conversations[user_id].append({'role': 'assistant', 'content': response})
        
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]
        
        return response
    
    def _build_context(self, user_id: int, user_message: str, result: Dict, username: str) -> str:
        """Build context string for Claude with operation results"""
        
        context_parts = [
            f"User: {username} (ID: {user_id})",
            f"Message: {user_message}",
            ""
        ]
        
        if result['success']:
            context_parts.append("✓ OPERATION SUCCESSFUL")
            context_parts.append(f"Result: {result['message']}")
            if 'data' in result:
                data = result['data']
                if 'balance' in data: context_parts.append(f"Balance: ${data['balance']:.2f}")
                if 'check_id' in data: context_parts.append(f"Check ID: {data['check_id']}")
                if 'checks' in data: context_parts.append(f"Total checks: {len(data['checks'])}")
                if 'history' in data: context_parts.append(f"Records: {len(data['history'])}")
        
        elif result.get('needs_clarification'):
            context_parts.append("⚠️ NEEDS CLARIFICATION")
            context_parts.append(f"Issue: {result['message']}")
            if 'ambiguities' in result:
                for amb in result['ambiguities']: context_parts.append(f"  - {amb}")
        
        elif result.get('layer2_not_available'):
            context_parts.append("ℹ️ LAYER 2 NOT AVAILABLE")
            context_parts.append(result['message'])
        
        else:
            context_parts.append("✗ OPERATION FAILED")
            context_parts.append(f"Error: {result['message']}")
        
        # Add intent info (SAFE JSON DUMP)
        if 'intent' in result:
            intent = result['intent']
            context_parts.append("")
            context_parts.append(f"Intent: {intent.operation}")
            context_parts.append(f"Confidence: {intent.confidence:.0%}")
            
            if intent.parameters:
                # --- FIX: Custom Date Serializer ---
                def json_serial(obj):
                    if isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    raise TypeError (f"Type {type(obj)} not serializable")
                
                try:
                    params_json = json.dumps(intent.parameters, indent=2, default=json_serial)
                    context_parts.append(f"Parameters: {params_json}")
                except Exception as e:
                    context_parts.append(f"Parameters: (Error displaying parameters: {e})")
        
        return "\n".join(context_parts)
    
    def _call_claude(self, user_id: int, user_message: str, context: str) -> str:
        """Call Claude API"""
        system_prompt = self._get_system_prompt()
        messages = self.conversations.get(user_id, []).copy()
        messages.append({
            'role': 'user',
            'content': f"{user_message}\n\n<operation_result>\n{context}\n</operation_result>"
        })
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."
    
    def _get_system_prompt(self) -> str:
        return """You are a friendly, professional banking assistant helping users manage POSTDATED checks.

**Your Role:**
- Help users issue, accept, deny, and forward POSTDATED checks
- Explain check operations clearly
- Maintain a warm, helpful tone

**CRITICAL - Postdated Check Mechanics:**
- ALL checks are POSTDATED - they mature at a future date
- NO immediate balance changes occur
- Issuing a check = Creating a commitment to pay at maturity
- Maturity date is when the issuer must finance the check

**Operation Handling:**
- Results are in <operation_result> tags
- If success: Confirm details (Amount, Name, Maturity Date)
- If failed: Explain why

**Example Responses:**
User: "Issue a check to Alice for $500 due Jan 1st"
You: "✓ Done! Check #123 to Alice for $500.00 is set. 📅 It matures on January 1, 2026."
"""

    def reset_conversation(self, user_id: int):
        if user_id in self.conversations:
            del self.conversations[user_id]