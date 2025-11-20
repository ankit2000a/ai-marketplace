"""
Escrow Manager
==============
The "Enforcer" - Manages locked funds to prevent agents from overcharging.
"""

from datetime import datetime, timezone
from typing import Dict, Optional
from decimal import Decimal

class InsufficientFundsError(Exception):
    pass

class OverchargeError(Exception):
    pass

class EscrowNotFoundError(Exception):
    pass

class EscrowManager:
    """
    Manages locked funds to prevent agents from overcharging
    """
    
    def __init__(self):
        self.escrows = {}  # job_id -> escrow_record
        self.agent_wallets = {}  # agent_name -> balance
        
        # Seed wallets for demo
        self.agent_wallets["PM_Budget"] = Decimal("10.00")
        self.agent_wallets["PM_Quality"] = Decimal("10.00")
        self.agent_wallets["PM_Balanced"] = Decimal("10.00")
    
    def get_balance(self, agent_id: str) -> float:
        # Return as float for API compatibility, but keep internal as Decimal
        return float(self.agent_wallets.get(agent_id, Decimal("0.00")))

    def create_escrow(self, job_id: str, buyer_id: str, max_price: float):
        """
        Lock buyer's funds when job is created
        """
        max_price_dec = Decimal(str(max_price))
        
        # Check buyer has sufficient balance
        buyer_balance = self.agent_wallets.get(buyer_id, Decimal("0.00"))
        if buyer_balance < max_price_dec:
            raise InsufficientFundsError(
                f"{buyer_id} has ${buyer_balance:.2f}, needs ${max_price_dec:.2f}"
            )
        
        # Lock the funds
        self.agent_wallets[buyer_id] -= max_price_dec
        
        self.escrows[job_id] = {
            "buyer": buyer_id,
            "seller": None,
            "max_price": max_price_dec,
            "actual_price": None,
            "locked_amount": max_price_dec,
            "status": "locked",
            "created_at": datetime.now(timezone.utc)
        }
        
        print(f"   🔒 Escrowed ${max_price_dec:.2f} for job {job_id} (Buyer: {buyer_id})")
    
    def release_payment(self, job_id: str, seller_id: str, actual_price: float):
        """
        Release payment after work is validated
        """
        actual_price_dec = Decimal(str(actual_price))
        
        escrow = self.escrows.get(job_id)
        if not escrow:
            raise EscrowNotFoundError(f"No escrow for job {job_id}")
        
        if escrow["status"] != "locked":
             raise ValueError(f"Escrow is not locked (Status: {escrow['status']})")

        # ENFORCE THE MAXIMUM PRICE
        if actual_price_dec > escrow["max_price"]:
            print(f"   ❌ OVERCHARGE DETECTED!")
            print(f"      Seller {seller_id} tried to charge ${actual_price_dec}")
            print(f"      Max allowed: ${escrow['max_price']}")
            print(f"      Payment REJECTED")
            
            # Refund buyer's locked funds
            self.agent_wallets[escrow["buyer"]] += escrow["locked_amount"]
            escrow["status"] = "rejected_overcharge"
            
            raise OverchargeError(
                f"Agent tried to charge ${actual_price_dec}, "
                f"max was ${escrow['max_price']}"
            )
        
        # Price is within limits, proceed
        # Pay seller
        self.agent_wallets[seller_id] = \
            self.agent_wallets.get(seller_id, Decimal("0.00")) + actual_price_dec
        
        # Refund buyer any unused funds
        refund = escrow["locked_amount"] - actual_price_dec
        self.agent_wallets[escrow["buyer"]] += refund
        
        # Update escrow record
        escrow["seller"] = seller_id
        escrow["actual_price"] = actual_price_dec
        escrow["status"] = "completed"
        
        print(f"   ✅ Released ${actual_price_dec:.2f} to {seller_id}")
        if refund > 0:
            print(f"   💰 Refunded ${refund:.2f} to {escrow['buyer']}")
            
    def refund(self, job_id: str):
        """
        Full refund if job fails or is cancelled
        """
        escrow = self.escrows.get(job_id)
        if not escrow:
            raise EscrowNotFoundError(f"No escrow for job {job_id}")
            
        if escrow["status"] != "locked":
             return # Already processed

        self.agent_wallets[escrow["buyer"]] += escrow["locked_amount"]
        escrow["status"] = "refunded"
        print(f"   ↩️  Refunded ${escrow['locked_amount']:.2f} to {escrow['buyer']}")

