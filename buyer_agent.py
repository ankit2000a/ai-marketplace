"""
Buyer Agent - Smart rating system based on multiple quality factors
"""
import httpx
import asyncio
import sys
import time

REGISTRY_URL = "http://127.0.0.1:8000"
CAPABILITY_NEEDED = "generate_charts"
BUYER_ID = "BuyerAgent_Main_v1"

PREFERENCES = {
    "price_weight": 0.3,
    "quality_weight": 0.4,
    "speed_weight": 0.2,
    "reliability_weight": 0.1
}

def calculate_rating(task_result: dict, response_time: float, expected_time: float) -> tuple[float, str]:
    rating = 5.0
    reasons = []
    
    status = task_result.get('status', 'unknown')
    if status != 'done':
        rating = 1.0
        reasons.append(f"Task failed (status: {status})")
        return rating, "; ".join(reasons)
    
    if response_time > expected_time * 2:
        rating -= 1.5
        reasons.append(f"Very slow ({response_time:.2f}s vs expected {expected_time:.2f}s)")
    elif response_time > expected_time * 1.5:
        rating -= 0.5
        reasons.append(f"Slower than expected ({response_time:.2f}s)")
    else:
        reasons.append(f"Good speed ({response_time:.2f}s)")
    
    result = task_result.get('result', '')
    
    if not result or len(result) < 10:
        rating -= 2.0
        reasons.append("Output is empty or too short")
    elif '[ERROR' in result or 'ERROR' in result:
        rating -= 1.5
        reasons.append("Result contains error message")
    elif 'MOCK' in result or 'mock' in result:
        rating -= 0.3
        reasons.append("Output is mock data (not real)")
    elif 'CHART' in result or 'PNG' in result or 'base64' in result:
        reasons.append("Valid chart data detected")
    else:
        rating -= 0.5
        reasons.append("Output format unclear")
    
    invoice = task_result.get('invoice', 0)
    expected_price = task_result.get('expected_price', invoice)
    if invoice > expected_price * 1.1:
        rating -= 0.5
        reasons.append(f"Overcharged")
    
    rating = max(1.0, min(5.0, rating))
    return rating, "; ".join(reasons)

async def main():
    print("🤖 BUYER AGENT STARTED")
    print("=" * 60)
    
    print("🎯 BUYER PREFERENCES:")
    for key, val in PREFERENCES.items():
        print(f"   {key}: {val*100}%")
    print("=" * 60)
    
    print(f"\n📍 STEP 1: Querying registry for '{CAPABILITY_NEEDED}'...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            search_response = await client.get(
                f"{REGISTRY_URL}/search",
                params={"capability": CAPABILITY_NEEDED, "limit": 5, **PREFERENCES}
            )
            if search_response.status_code == 404:
                print(f"❌ No agents found")
                sys.exit(1)
            search_response.raise_for_status()
            candidates = search_response.json()
    except httpx.ConnectError:
        print("❌ Registry unreachable.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    if isinstance(candidates, dict):
        candidates = [candidates]
    if not candidates:
        sys.exit(1)
    
    print(f"\n✅ STEP 2: Found {len(candidates)} candidate(s):")
    print("=" * 60)
    
    for i, agent in enumerate(candidates, 1):
        print(f"\n{i}. {agent['name']}")
        print(f"   💰 Price: ${agent['price']}")
        print(f"   ⭐ Rating: {agent['rating']:.2f}/5.0")
        print(f"   📊 Total Jobs: {agent['total_jobs']}")
    
    selected = candidates[0]
    expected_response_time = selected['avg_response_time']
    
    print(f"\n🎯 SELECTED: {selected['name']}")
    print(f"\n📍 STEP 3: Hiring...")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            task_response = await client.post(
                f"{selected['url']}/execute_task",
                json={"task_data": "Create pie chart of user demographics"}
            )
            task_response.raise_for_status()
            task_result = task_response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    actual_response_time = time.time() - start_time
    
    print(f"\n✅ STEP 4: Task completed in {actual_response_time:.2f}s!")
    
    final_invoice = task_result.get('invoice', selected['price'])
    task_result['expected_price'] = selected['price']
    
    print(f"\n📍 STEP 5: Reporting transaction...")
    
    tx_id = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            rep = await client.post(f"{REGISTRY_URL}/report_transaction", json={
                "buyer_id": BUYER_ID,
                "seller_name": selected['name'],
                "capability": CAPABILITY_NEEDED,
                "price": final_invoice
            })
            rep.raise_for_status()
            tx_id = rep.json().get("transaction_id")
            print(f"✅ Transaction logged. transaction_id={tx_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print(f"\n📍 STEP 6: Calculating rating...")
    
    calculated_rating, rating_reason = calculate_rating(task_result, actual_response_time, expected_response_time)
    
    print(f"   📈 CALCULATED RATING: {calculated_rating:.1f}/5.0")
    print(f"   📝 Reason: {rating_reason}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            rate_resp = await client.post(f"{REGISTRY_URL}/rate_transaction", json={
                "transaction_id": tx_id,
                "rating": calculated_rating,
                "feedback": rating_reason,
                "would_hire_again": calculated_rating >= 4.0
            })
            rate_resp.raise_for_status()
            new_rating = rate_resp.json().get('new_rating', 'N/A')
            print(f"\n✅ Agent's updated rating: {new_rating:.2f}/5.0")
    except Exception as e:
        print(f"⚠️ Could not submit rating: {e}")
    
    print("\n✅ BUYER AGENT COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(main())