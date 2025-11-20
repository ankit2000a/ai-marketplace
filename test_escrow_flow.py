import requests
import uuid
import time

REGISTRY_URL = "http://127.0.0.1:8000"
BUYER_ID = "PM_Budget"

def test_escrow_flow():
    print("🚀 Testing Escrow Flow")
    
    # 1. Check initial balance
    resp = requests.get(f"{REGISTRY_URL}/wallet/balance/{BUYER_ID}")
    initial_balance = resp.json()["balance"]
    print(f"   💰 Initial Balance: ${initial_balance}")
    
    # 2. Create Escrow
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    max_price = 0.05
    print(f"   🔒 Creating Escrow for ${max_price}...")
    resp = requests.post(f"{REGISTRY_URL}/escrow/create", json={
        "job_id": job_id,
        "buyer_id": BUYER_ID,
        "max_price": max_price
    })
    if resp.status_code == 200:
        print("   ✅ Escrow created")
    else:
        print(f"   ❌ Failed: {resp.text}")
        return

    # 3. Check balance (should be lower)
    resp = requests.get(f"{REGISTRY_URL}/wallet/balance/{BUYER_ID}")
    locked_balance = resp.json()["balance"]
    print(f"   💰 Balance after lock: ${locked_balance}")
    
    if locked_balance != initial_balance - max_price:
        print("   ❌ Balance mismatch!")
    
    # 4. Release Payment (Normal)
    print("   💸 Releasing Payment ($0.03)...")
    resp = requests.post(f"{REGISTRY_URL}/escrow/release", json={
        "job_id": job_id,
        "seller_id": "ChartBot_Budget_v1",
        "actual_price": 0.03
    })
    if resp.status_code == 200:
        print("   ✅ Payment released")
    else:
        print(f"   ❌ Failed: {resp.text}")

    # 5. Check balance (refund should happen)
    # Locked 0.05, Paid 0.03, Refund 0.02. Balance should be Initial - 0.03
    resp = requests.get(f"{REGISTRY_URL}/wallet/balance/{BUYER_ID}")
    final_balance = resp.json()["balance"]
    print(f"   💰 Final Balance: ${final_balance}")
    
    if abs(final_balance - (initial_balance - 0.03)) < 0.001:
        print("   ✅ Balance correct (Refund received)")
    else:
        print(f"   ❌ Balance incorrect. Expected {initial_balance - 0.03}, got {final_balance}")

def test_overcharge():
    print("\n🚨 Testing Overcharge Protection")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    max_price = 0.05
    
    requests.post(f"{REGISTRY_URL}/escrow/create", json={
        "job_id": job_id,
        "buyer_id": BUYER_ID,
        "max_price": max_price
    })
    
    print("   💸 Attempting to charge $0.10 (Limit $0.05)...")
    resp = requests.post(f"{REGISTRY_URL}/escrow/release", json={
        "job_id": job_id,
        "seller_id": "ChartBot_Budget_v1",
        "actual_price": 0.10
    })
    
    if resp.status_code == 400:
        print(f"   ✅ Blocked correctly: {resp.json()['detail']}")
    else:
        print(f"   ❌ FAILED: Should have blocked but got {resp.status_code}")

if __name__ == "__main__":
    test_escrow_flow()
    test_overcharge()
