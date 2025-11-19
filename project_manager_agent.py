"""
Project Manager Agent (Smart Selection)
=======================================
This agent acts as a BUYER that orchestrates multiple specialist agents.
Now supports:
- Softmax/Weighted Lottery selection
- Result validation & Escrow
- Configurable strategies (Budget, Quality, Balanced)

Capabilities:
- Hires text summarization agents
- Hires chart generation agents
- Compiles results into comprehensive reports
- Manages costs and transactions

Price: $0.10 per orchestration
"""

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
import uvicorn
import requests
import json
import random
import math
import argparse
import sys

# ============================================================
# CONFIGURATION
# ============================================================
AGENT_NAME = "ProjectManager"
AGENT_PORT = 8001
CAPABILITY = "project_orchestration"
AGENT_PRICE = 0.10
REGISTRY_URL = "http://127.0.0.1:8000"

# Default Strategy (Balanced)
PM_STRATEGY = "balanced"
SELECTION_WEIGHTS = {
    'price': 0.4,
    'quality': 0.4,
    'speed': 0.2
}
SELECTION_TEMPERATURE = 1.0

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title=AGENT_NAME)

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class TaskRequest(BaseModel):
    task_data: str | dict

class TaskResponse(BaseModel):
    status: str
    report_title: str
    summary_component: str
    chart_component: str
    total_cost_incurred: float
    final_invoice: float
    completed_at: str

# ============================================================
# SMART SELECTION LOGIC
# ============================================================

def softmax_select_agent(candidates, weights, temperature=1.0):
    """
    Weighted lottery selection using Softmax
    
    Args:
        candidates: List of agents from registry
        weights: {'price': 0.4, 'quality': 0.4, 'speed': 0.2}
        temperature: 0.1=greedy, 10.0=random, 1.0=balanced
    
    Returns:
        Selected agent
    """
    if not candidates:
        return None
    
    if len(candidates) == 1:
        print(f"   🎰 SINGLE CANDIDATE (No lottery needed):")
        print(f"      🏆 {candidates[0]['name']} (Only match found)")
        return candidates[0]
    
    # Calculate scores for each agent
    scores = []
    for agent in candidates:
        # Price score (lower is better, so invert)
        max_price = max(c['price'] for c in candidates)
        price_score = (max_price - agent['price']) / max_price if max_price > 0 else 0
        
        # Quality score (higher is better)
        quality_score = agent.get('rating', 3.0) / 5.0
        
        # Speed score (lower latency is better)
        max_latency = max(c.get('avg_response_time', 1.0) for c in candidates)
        speed_score = (max_latency - agent.get('avg_response_time', 0.5)) / max_latency if max_latency > 0 else 0
        
        # Weighted total
        final_score = (
            price_score * weights.get('price', 0.4) +
            quality_score * weights.get('quality', 0.4) +
            speed_score * weights.get('speed', 0.2)
        )
        
        scores.append(final_score)
    
    # Apply softmax
    try:
        exp_scores = [math.exp(s / temperature) for s in scores]
    except OverflowError:
        # Handle overflow by scaling down or just using max
        max_s = max(scores)
        exp_scores = [math.exp((s - max_s) / temperature) for s in scores]

    total_exp = sum(exp_scores)
    if total_exp == 0:
        probabilities = [1.0 / len(candidates)] * len(candidates)
    else:
        probabilities = [s / total_exp for s in exp_scores]
    
    # Weighted lottery
    selected = random.choices(candidates, weights=probabilities, k=1)[0]
    
    # Log the lottery results
    print(f"   🎰 LOTTERY RESULTS (Temp={temperature}):")
    for agent, prob in zip(candidates, probabilities):
        mark = "🏆" if agent == selected else "  "
        print(f"      {mark} {agent['name']}: {prob*100:.1f}% chance (Score: {scores[candidates.index(agent)]:.2f})")
    
    return selected

# ============================================================
# VALIDATION LOGIC
# ============================================================

def validate_chart_result(result):
    """Validate chart generation result"""
    if not result:
        return False, "Empty result"
    
    if isinstance(result, dict) and 'error' in result:
        return False, f"Agent error: {result.get('error')}"
    
    # Check if base64 image
    if isinstance(result, str):
        if len(result) < 100:
            return False, "Result too short to be valid image"
        
        # Basic base64 check
        try:
            import base64
            # Check if it looks like base64 (alphanumeric + +/=)
            # This is a loose check
            if " " in result[:50]: 
                return False, "Contains spaces, likely not base64"
            return True, "Valid"
        except:
            return False, "Invalid base64 encoding"
    
    return True, "Valid"

def validate_summary_result(result):
    """Validate summary result"""
    if not result:
        return False, "Empty summary"
    
    if isinstance(result, str):
        if len(result) < 10:
            return False, "Summary too short"
        return True, "Valid"
    
    return False, "Invalid summary format"

# ============================================================
# HELPER FUNCTION: HIRE SPECIALISTS
# ============================================================

def hire_specialist(capability: str, task_data):
    """
    Hire specialist with validation and conditional payment
    """
    print(f"   🔍 Searching registry for: {capability}")
    
    try:
        # Search registry
        # Apply filters based on strategy
        params = {"capability": capability}
        if PM_STRATEGY == "cost_minimization":
            params["max_price"] = 0.04
        elif PM_STRATEGY == "quality_maximization":
            params["min_rating"] = 4.0
            
        search_response = requests.get(
            f"{REGISTRY_URL}/search",
            params=params,
            timeout=5
        )
        
        agents = []
        if search_response.status_code == 200:
            agents = search_response.json()
        
        # Fallback: if strict filters return nothing, try without filters
        if not agents and (PM_STRATEGY == "cost_minimization" or PM_STRATEGY == "quality_maximization"):
            print(f"   ⚠️ No agents found with strict {PM_STRATEGY} filters. Relaxing constraints...")
            search_response = requests.get(
                f"{REGISTRY_URL}/search",
                params={"capability": capability},
                timeout=5
            )
            if search_response.status_code == 200:
                agents = search_response.json()

        if not agents:
            return {"error": f"No agents found for capability: {capability}"}
        
        # SMART SELECTION
        selected_agent = softmax_select_agent(agents, SELECTION_WEIGHTS, temperature=SELECTION_TEMPERATURE)
        
        if not selected_agent:
            return {"error": "Agent selection failed"}

        agent_name = selected_agent['name']
        agent_url = selected_agent['url']
        agent_price = selected_agent['price']
        
        print(f"   🔄 Calling {agent_name}...")
        
        # Call agent
        response = requests.post(
            agent_url,
            json={"task_data": task_data},
            timeout=30
        )
        
        if response.status_code == 200:
            result_data = response.json()
            result = result_data.get("result")
            
            # VALIDATE RESULT
            if capability == "generate_charts":
                is_valid, msg = validate_chart_result(result)
            elif capability == "summarize_text":
                is_valid, msg = validate_summary_result(result)
            else:
                is_valid, msg = True, "No validator"
            
            if is_valid:
                # ONLY pay if valid!
                print(f"   ✅ Result validated: {msg}")
                
                # Report successful transaction
                try:
                    requests.post(
                        f"{REGISTRY_URL}/report_transaction",
                        json={
                            "buyer_id": AGENT_NAME,
                            "seller_name": agent_name,
                            "amount": agent_price,
                            "success": True
                        },
                        timeout=5
                    )
                except:
                    pass
                
                return {
                    "agent_name": agent_name,
                    "result": result,
                    "invoice": agent_price
                }
            else:
                # FAILED validation - no payment!
                print(f"   ❌ Validation failed: {msg}")
                
                # Report failed transaction (penalty to reputation)
                try:
                    requests.post(
                        f"{REGISTRY_URL}/report_transaction",
                        json={
                            "buyer_id": AGENT_NAME,
                            "seller_name": agent_name,
                            "amount": 0.0,
                            "success": False
                        },
                        timeout=5
                    )
                except:
                    pass
                
                # Retry logic could go here (e.g. try 2nd best), but for now return error
                return {"error": f"Validation failed: {msg}"}
        
        else:
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {"error": str(e)}

# ============================================================
# MAIN ENDPOINT: ORCHESTRATE TASKS
# ============================================================

@app.post("/execute_task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    PROJECT MANAGER's main execution logic.
    """
    print(f"\n{'='*60}")
    print(f"🎯 PROJECT MANAGER ({PM_STRATEGY}): New job received!")
    print(f"📋 Task: {request.task_data}")
    print(f"⏰ Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*60}")
    print("🤖 PROJECT MANAGER: Analyzing task and hiring specialists...\n")
    
    # Track costs
    total_cost = 0.0
    
    # ========================================
    # STEP 1: HIRE TEXT SUMMARIZER
    # ========================================
    print("📍 STEP 1: Hiring text summarization specialist...")
    
    # Prepare summarization task
    if isinstance(request.task_data, dict):
        text_to_summarize = request.task_data.get("text_to_summarize", str(request.task_data))
    else:
        text_to_summarize = str(request.task_data)
    
    summary_result = hire_specialist(
        capability="summarize_text",
        task_data=text_to_summarize
    )
    
    if summary_result.get("error"):
        print(f"   ❌ Summarization failed: {summary_result['error']}")
        summary_component = f"[ERROR: {summary_result['error']}]"
        summary_cost = 0.0
    else:
        print(f"   ✅ Summary complete from {summary_result['agent_name']}")
        summary_component = summary_result["result"]
        summary_cost = summary_result["invoice"]
        total_cost += summary_cost
    
    # ========================================
    # STEP 2: HIRE CHART GENERATOR
    # ========================================
    print("\n📍 STEP 2: Hiring chart generation specialist...")
    
    # Prepare chart task (with proper format!)
    chart_task_data = {
        "chart_type": "bar",
        "data": {
            "categories": ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"],
            "values": [120, 150, 180, 210],
            "title": "AI Marketplace Growth Projection",
            "xlabel": "Quarter",
            "ylabel": "Revenue ($K)"
        }
    }
    
    chart_result = hire_specialist(
        capability="generate_charts",
        task_data=chart_task_data
    )
    
    if chart_result.get("error"):
        print(f"   ❌ Chart generation failed: {chart_result['error']}")
        chart_component = f"[ERROR: {chart_result['error']}]"
        chart_cost = 0.0
    else:
        print(f"   ✅ Chart complete from {chart_result['agent_name']}")
        chart_component = chart_result["result"]
        chart_cost = chart_result["invoice"]
        total_cost += chart_cost
        print(f"   📏 Chart size: {len(chart_component)} bytes (base64 PNG)")
    
    # ========================================
    # STEP 3: COMPILE FINAL REPORT
    # ========================================
    print(f"\n📍 STEP 3: Compiling final report...")
    print(f"   💰 Summarization cost: ${summary_cost:.2f}")
    print(f"   💰 Chart generation cost: ${chart_cost:.2f}")
    print(f"   💰 Total specialist costs: ${total_cost:.2f}")
    print(f"   💰 Project Manager fee: ${AGENT_PRICE:.2f}")
    print(f"   💰 GRAND TOTAL: ${total_cost + AGENT_PRICE:.2f}")
    print("\n✅ PROJECT MANAGER: All tasks complete! Delivering final report.")
    print(f"{'='*60}\n")
    
    # Return comprehensive response
    return TaskResponse(
        status="done",
        report_title=f"Market Analysis Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        summary_component=summary_component,
        chart_component=chart_component,
        total_cost_incurred=total_cost,
        final_invoice=AGENT_PRICE,
        completed_at=datetime.now(timezone.utc).isoformat()
    )

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": AGENT_NAME,
        "capability": CAPABILITY,
        "price": AGENT_PRICE,
        "strategy": PM_STRATEGY
    }

# ============================================================
# STARTUP: REGISTER WITH REGISTRY
# ============================================================

@app.on_event("startup")
async def startup_event():
    print(f"\n🤖 {AGENT_NAME} starting up...")
    print(f"   Strategy: {PM_STRATEGY}")
    print(f"   Weights: {SELECTION_WEIGHTS}")
    
    # Register with registry
    registration_data = {
        "name": AGENT_NAME,
        "capability": CAPABILITY,
        "url": f"http://127.0.0.1:{AGENT_PORT}/execute_task",
        "price": AGENT_PRICE,
        "description": f"Orchestrates multiple specialists ({PM_STRATEGY})"
    }
    
    try:
        requests.post(f"{REGISTRY_URL}/register", json=registration_data, timeout=5)
        print(f"✅ Registered with registry")
    except:
        print(f"⚠️  Registry not reachable")

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--strategy", type=str, default="balanced", choices=["balanced", "budget", "quality"])
    args = parser.parse_args()
    
    AGENT_PORT = args.port
    
    # Configure Strategy
    if args.strategy == "budget":
        PM_STRATEGY = "cost_minimization"
        SELECTION_WEIGHTS = {'price': 0.8, 'quality': 0.1, 'speed': 0.1}
        SELECTION_TEMPERATURE = 0.5
        AGENT_NAME = "PM_Budget"
    elif args.strategy == "quality":
        PM_STRATEGY = "quality_maximization"
        SELECTION_WEIGHTS = {'price': 0.1, 'quality': 0.8, 'speed': 0.1}
        SELECTION_TEMPERATURE = 0.5
        AGENT_NAME = "PM_Quality"
    else:
        PM_STRATEGY = "balanced"
        SELECTION_WEIGHTS = {'price': 0.4, 'quality': 0.4, 'speed': 0.2}
        SELECTION_TEMPERATURE = 1.0
        AGENT_NAME = "PM_Balanced"
        
    print(f"🚀 Starting {AGENT_NAME} on port {AGENT_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=AGENT_PORT)