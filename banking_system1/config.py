"""
Configuration for Conversational Banking System
==============================================
"""

import os

# Anthropic API Configuration
ANTHROPIC_API_KEY = "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"
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Latest Sonnet model

# Database Configuration
DATABASE_PATH = "banking_system.db"

# System Configuration
DEFAULT_USER_BALANCE = 10000.0  # Starting balance for demo users
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to auto-execute
CLARIFICATION_THRESHOLD = 0.4  # Below this, ask for clarification

# Layer 2 Configuration (Future)
LAYER_2_ENABLED = False  # Set to True when tokenization is ready
TOKENIZATION_DEFAULT_DISCOUNT = 5.0  # Default discount rate for tokenization

# Demo Configuration
DEMO_MODE = True  # Show extra helpful messages
VERBOSE_LOGGING = True  # Log operations to console
