import requests
import json
import time

def test_pm(name, port, iterations=5):
    print(f"\n🧪 Testing {name} (Port {port})...")
    url = f"http://127.0.0.1:{port}/execute_task"
    
    counts = {}
    
    for i in range(iterations):
        try:
            response = requests.post(url, json={"task_data": "Test summary"}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Parse logs or assume success means it worked. 
                # But we want to know WHICH agent was picked.
                # The response doesn't explicitly say which agent was picked for subtasks, 
                # but we can infer from cost or maybe we should have exposed it.
                # Wait, the response has total_cost_incurred.
                # ChartBot Budget is $0.03, Pro is $0.05.
                # Summarizer is $0.02.
                # So total cost = 0.02 + ChartBot cost.
                # If total cost ~ 0.05 -> Budget ($0.02 + $0.03)
                # If total cost ~ 0.07 -> Pro ($0.02 + $0.05)
                
                cost = data.get("total_cost_incurred", 0)
                if abs(cost - 0.05) < 0.001:
                    agent = "ChartBot_Budget"
                elif abs(cost - 0.07) < 0.001:
                    agent = "ChartBot_Pro"
                else:
                    agent = f"Unknown (Cost: {cost})"
                
                counts[agent] = counts.get(agent, 0) + 1
                print(f"   Run {i+1}: {agent} (Cost: ${cost:.2f})")
            else:
                print(f"   Run {i+1}: Failed (HTTP {response.status_code})")
        except Exception as e:
            print(f"   Run {i+1}: Error ({str(e)})")
            
    print(f"   📊 Results for {name}: {counts}")

if __name__ == "__main__":
    # Give services time to start
    time.sleep(2)
    
    test_pm("PM Budget", 8001, iterations=5)
    test_pm("PM Quality", 8005, iterations=5)
    test_pm("PM Balanced", 8006, iterations=5)
