"""
Check Manager - Layer 1 Banking Operations
==========================================
Manages the lifecycle of checks.
UPDATED: 
- Persistent IDs (Forwarding updates the owner, doesn't create new check)
- Local Time usage for correct 1-hour limits
- Fuzzy User Resolution (Fixes "Alice" vs "Alice Corp")
- Smart Sender Restoration on Cancel (Fixes disappearing checks)
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import sqlite3

class CheckManager:
    """
    Central logic for all Check operations.
    Interacts directly with the database.
    """
    
    def __init__(self, db_manager, entity_manager):
        self.db = db_manager
        self.entity_mgr = entity_manager
        self._ensure_columns()
        
    def _ensure_columns(self):
        """Ensures schema compatibility."""
        try:
            # We need sender_id for the persistent forward logic
            self.db.conn.execute("ALTER TABLE checks ADD COLUMN sender_id INTEGER REFERENCES users(id)")
            self.db.conn.commit()
        except sqlite3.OperationalError:
            pass

    # --- ISSUANCE ---
    def issue_check(self, issuer_id: int, payee_name: str, amount: float, custom_date: Optional[datetime] = None, days_to_maturity: int = 0) -> Tuple[bool, str, Optional[int]]:
        """Creates a new check."""
        now = datetime.now() # Use Local Time
        maturity_date = custom_date if custom_date else now + timedelta(days=days_to_maturity)
        
        cursor = self.db.conn.cursor()
        payee_id = self._resolve_user(payee_name)
        
        try:
            # Initial sender_id is the issuer (optional, but good for tracking)
            cursor.execute("""
                INSERT INTO checks (issuer_id, payee_id, sender_id, amount, status, maturity_date, issued_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?, ?)
            """, (issuer_id, payee_id, issuer_id, amount, maturity_date, now))
            
            check_id = cursor.lastrowid
            self.db.conn.commit()
            return True, f"Check #{check_id} issued to {payee_name}.", check_id
        except Exception as e:
            self.db.conn.rollback()
            return False, f"Error issuing check: {e}", None

    # --- STATUS CHANGES ---
    def accept_check(self, user_id: int, check_id: int = None, issuer_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Marks a check as ACCEPTED."""
        cursor = self.db.conn.cursor()
        
        if check_id:
            cursor.execute("SELECT * FROM checks WHERE id=? AND payee_id=? AND status IN ('PENDING', 'DENIED')", (check_id, user_id))
        elif issuer_name:
            # Resolves issuer name fuzzily to find pending checks
            issuer_id_candidate = self._resolve_user(issuer_name)
            cursor.execute("""
                SELECT c.* FROM checks c 
                WHERE c.payee_id = ? AND c.status IN ('PENDING', 'DENIED') 
                AND c.sender_id = ? LIMIT 1
            """, (user_id, issuer_id_candidate))
        else:
            return False, "Missing check information", None
        
        check = cursor.fetchone()
        if not check:
            return False, "Check not found or not available to accept.", None
        
        # Transaction Complete: Clear sender_id so previous owner can't pull it back anymore
        cursor.execute("UPDATE checks SET status='ACCEPTED', sender_id=NULL WHERE id=?", (check['id'],))
        self.db.conn.commit()
        return True, f"Check #{check['id']} Accepted", check['id']

    def deny_check(self, user_id: int, check_id: int = None, issuer_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """Marks a check as DENIED."""
        cursor = self.db.conn.cursor()
        
        if check_id:
            cursor.execute("SELECT * FROM checks WHERE id=? AND payee_id=? AND status IN ('PENDING', 'ACCEPTED')", (check_id, user_id))
        elif issuer_name:
            issuer_id_candidate = self._resolve_user(issuer_name)
            cursor.execute("""
                SELECT c.* FROM checks c 
                WHERE c.payee_id = ? AND c.status IN ('PENDING', 'ACCEPTED') 
                AND c.sender_id = ? LIMIT 1
            """, (user_id, issuer_id_candidate))
        else:
            return False, "Missing check information", None
        
        check = cursor.fetchone()
        if not check:
            return False, "Check not found.", None
        
        cursor.execute("UPDATE checks SET status='DENIED' WHERE id=?", (check['id'],))
        self.db.conn.commit()
        return True, f"Check #{check['id']} Denied", check['id']

    # --- FORWARDING (PERSISTENT ID) ---
    def forward_check(self, user_id: int, check_id: int, new_payee_name: str) -> Tuple[bool, str, Optional[int]]:
        """
        Forwards a check by transferring ownership.
        Does NOT create a new check row.
        """
        cursor = self.db.conn.cursor()
        
        # 1. Verify Ownership (Must be ACCEPTED and in my wallet)
        cursor.execute("SELECT * FROM checks WHERE id=? AND payee_id=? AND status='ACCEPTED'", (check_id, user_id))
        check = cursor.fetchone()
        
        if not check:
            return False, "Check not found, not accepted, or you do not own it.", None
        
        new_payee_id = self._resolve_user(new_payee_name)
        now = datetime.now()
        
        # 2. Transfer Ownership
        # Set Payee = New Person
        # Set Sender = Me (so I can cancel it later if needed)
        # Set Status = PENDING (waiting for them to accept)
        cursor.execute("""
            UPDATE checks 
            SET payee_id = ?, sender_id = ?, status = 'PENDING', issued_at = ?
            WHERE id = ?
        """, (new_payee_id, user_id, now, check_id))
        
        self.db.conn.commit()
        return True, f"Check #{check_id} forwarded to {new_payee_name}.", check_id

    # --- REVOKE / CANCEL LOGIC ---
    def cancel_forward(self, user_id: int, check_id: int) -> Tuple[bool, str]:
        """
        Pulls back a forwarded check.
        FIX: Restores correct sender_id to prevent check from disappearing.
        """
        cursor = self.db.conn.cursor()
        
        # Find check where I am the Sender and it is Pending
        cursor.execute("SELECT * FROM checks WHERE id=? AND sender_id=? AND status='PENDING'", (check_id, user_id))
        check = cursor.fetchone()
        
        if not check:
            return False, "Cannot cancel: Check not found, already accepted by recipient, or not sent by you."
        
        # Time Limit Check
        try:
            sent_time = datetime.fromisoformat(check['issued_at'])
            if (datetime.now() - sent_time).total_seconds() > 3600:
                return False, "Cannot cancel: 1-hour revocation window has expired."
        except: pass 
        
        # FIX: Determine correct restoration state
        # If I am the Issuer, I want sender_id to be ME (so it looks like an issued check I hold).
        # If I am NOT the Issuer, sender_id should be NULL (so it looks like an accepted check I hold).
        new_sender_id = user_id if check['issuer_id'] == user_id else None

        # Revert Ownership
        cursor.execute("""
            UPDATE checks 
            SET payee_id = ?, sender_id = ?, status = 'ACCEPTED'
            WHERE id = ?
        """, (user_id, new_sender_id, check_id))
        
        self.db.conn.commit()
        return True, f"Forward for Check #{check_id} cancelled. It has been returned to your wallet."

    def cancel_issuance(self, user_id: int, check_id: int) -> Tuple[bool, str]:
        """Hard delete of an issued check."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM checks WHERE id=? AND issuer_id=? AND status='PENDING'", (check_id, user_id))
        check = cursor.fetchone()
        
        if not check:
            return False, "Cannot cancel: Check not found or recipient has already processed it."
        
        # Time Limit Check
        try:
            issued = datetime.fromisoformat(check['issued_at'])
            if (datetime.now() - issued).total_seconds() > 3600:
                return False, "Cannot cancel: 1-hour revocation window has expired."
        except: pass
        
        cursor.execute("DELETE FROM checks WHERE id=?", (check_id,))
        self.db.conn.commit()
        return True, f"Issuance of Check #{check_id} cancelled."

    def revoke_incoming_decision(self, user_id: int, check_id: int) -> Tuple[bool, str]:
        """Reset decision (Accept/Deny) back to PENDING."""
        cursor = self.db.conn.cursor()
        # Verify I am the payee
        cursor.execute("SELECT * FROM checks WHERE id=? AND payee_id=?", (check_id, user_id))
        if not cursor.fetchone():
            return False, "You do not own this check."
            
        cursor.execute("UPDATE checks SET status='PENDING' WHERE id=?", (check_id,))
        self.db.conn.commit()
        return True, f"Decision reset. Check #{check_id} is back to PENDING status."

    # --- HELPERS ---
    def get_user_checks(self, user_id: int, filter_type: str = 'all') -> List[Dict]:
        cursor = self.db.conn.cursor()
        # Query gets: Checks I Issued OR Checks I have (Payee) OR Checks I sent (Sender)
        query = """
            SELECT c.*, 
                   u1.username as issuer_name, 
                   u2.username as payee_name,
                   u3.username as sender_name
            FROM checks c
            JOIN users u1 ON c.issuer_id = u1.id
            JOIN users u2 ON c.payee_id = u2.id
            LEFT JOIN users u3 ON c.sender_id = u3.id
            WHERE c.issuer_id = ? OR c.payee_id = ? OR c.sender_id = ?
            ORDER BY c.id DESC
        """
        cursor.execute(query, (user_id, user_id, user_id))
        
        checks = []
        for row in cursor.fetchall():
            c = dict(row)
            
            # --- BASKET LOGIC ---
            # 1. Checks I currently hold
            if c['payee_id'] == user_id:
                if c['status'] == 'ACCEPTED':
                    c['category'] = 'WALLET'
                elif c['status'] == 'DENIED':
                    c['category'] = 'DENIED_HISTORY'
                else:
                    c['category'] = 'INCOMING'
            
            # 2. Checks I created (Original Issuer)
            elif c['issuer_id'] == user_id:
                c['category'] = 'ISSUED'
                
            # 3. Checks I forwarded (I am sender, but NOT the original issuer)
            elif c['sender_id'] == user_id and c['issuer_id'] != user_id:
                c['category'] = 'FORWARDED'
            
            else:
                c['category'] = 'OTHER'

            checks.append(c)
            
        return checks

    def get_user_balance(self, uid: int) -> float:
        res = self.db.conn.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
        return res[0] if res else 0.0

    def _resolve_user(self, name: str) -> int:
        """
        Robust User Resolution (Fuzzy Matching + Auto Create)
        Fixes issue where 'Alice' creates a new user instead of matching 'Alice Corporation'.
        """
        cursor = self.db.conn.cursor()
        clean_name = name.strip()
        
        # 1. Search Exact Case-Insensitive
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (clean_name,))
        res = cursor.fetchone()
        if res:
            return res[0]
        
        # 2. Fuzzy Match (Contains)
        # matches "Alice" to "Alice Corporation"
        cursor.execute("SELECT id FROM users WHERE LOWER(username) LIKE ?", (f"%{clean_name.lower()}%",))
        results = cursor.fetchall()
        
        if len(results) == 1:
            # If exactly one match found, assume that's the one
            return results[0][0]
            
        # 3. Create if not exists (or if ambiguous)
        try:
            cursor.execute("INSERT INTO users (username, balance) VALUES (?, 0)", (clean_name,))
            self.db.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Fallback for race condition
            cursor.execute("SELECT id FROM users WHERE username = ?", (clean_name,))
            return cursor.fetchone()[0]