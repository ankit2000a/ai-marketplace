import requests
import json
import time
import subprocess
import sys
import uuid
from a2a_protocol import JobOffer, JobConstraints

# Configuration
REGISTRY_URL = "http://127.0.0.1:8000"
AGENT_URL = "http://127.0.0.1:8004" # ChartBot Budget
PM_URL = "http://127.0.0.1:8001"

def test_agent_card():
    print("\n🔍 Testing Agent Card...")
    try:
        resp = requests.get(f"{AGENT_URL}/.well-known/agent.json")
        if resp.status_code == 200:
            card = resp.json()
            print(f"   ✅ Agent Card found: {card['agent']['name']}")
            print(f"      Price: {card['pricing']['amount']} {card['pricing']['currency']}")
        else:
            print(f"   ❌ Failed to get Agent Card: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_job_rejection_and_acceptance(): # Renamed function to reflect combined tests
    # 2. Test Job Rejection (Budget too low)
    print("\n2. Testing Job Rejection (Low Budget)...")
    low_budget_offer = JobOffer(
        job_id=f"test_job_{uuid.uuid4().hex[:8]}",
        buyer_id="Test_Script",
        capability="generate_charts",
        constraints=JobConstraints(
            max_price=0.01,  # Too low (Price is 0.03)
            max_latency_ms=5000
        ),
        task_payload={
            "chart_type": "pie", 
            "data": {"values": [10, 20, 30], "labels": ["A", "B", "C"]}
        }
    )
    
    try:
        resp = requests.post(f"{AGENT_URL}/execute_task", json=low_budget_offer.model_dump())
        print(f"   Status Code: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            if result.get("status") == "rejected":
                print(f"   ✅ Correctly rejected: {result.get('error')}")
            else:
                print(f"   ❌ Failed: Should have rejected but got {result.get('status')}")
        else:
            print(f"   ❌ Failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 3. Test Job Acceptance (Budget sufficient)
    print("\n3. Testing Job Acceptance (Sufficient Budget)...")
    good_offer = JobOffer(
        job_id=f"test_job_{uuid.uuid4().hex[:8]}",
        buyer_id="Test_Script",
        capability="generate_charts",
        constraints=JobConstraints(
            max_price=0.05,  # Sufficient (Price is 0.03)
            max_latency_ms=5000
        ),
        task_payload={
            "chart_type": "pie", 
            "data": {"values": [10, 20, 30], "labels": ["A", "B", "C"]}
        }
    )
    
    try:
        resp = requests.post(f"{AGENT_URL}/execute_task", json=good_offer.model_dump())
        if resp.status_code == 200:
            result = resp.json()
            if result.get("status") == "done":
                print(f"   ✅ Correctly accepted. Invoice: ${result.get('invoice')}")
            else:
                print(f"   ❌ Failed: Should have accepted but got {result.get('status')}")
        else:
            print(f"   ❌ Failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting A2A Protocol Verification")
    test_agent_card()
    test_job_rejection_and_acceptance()
