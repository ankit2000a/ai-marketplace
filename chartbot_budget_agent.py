"""
ChartBot Pro v1 - Premium Chart Generation Agent
Generates high-quality charts using matplotlib
Price: $0.05 per chart
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uvicorn
import requests
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import json

# ============================================================
# CONFIGURATION
# ============================================================
AGENT_NAME = "ChartBot_Budget_v1"  # ← Change
AGENT_PORT = 8004  # ← Change
CAPABILITY = "generate_charts"  # ← Keep same
PRICE_PER_TASK = 0.03  # ← Change
REGISTRY_URL = "http://127.0.0.1:8000"  # ← Keep same

# Chart settings (lower quality)
CHART_DPI = 72  # ← Change from 150
CHART_FIGSIZE = (8, 5)  # ← Change from (10, 6)
CHART_STYLE = 'default'  # ← Change from 'seaborn-v0_8-darkgrid'

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title=AGENT_NAME)

from a2a_protocol import JobOffer, AgentCard

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title=AGENT_NAME)

class TaskResult(BaseModel):
    status: str
    result: str  # Base64 encoded PNG
    invoice: float
    completed_at: str
    error: Optional[str] = None


# ============================================================
# CHART GENERATION FUNCTIONS
# ============================================================

def generate_pie_chart(data: dict) -> str:
    """Generate pie chart and return base64 PNG"""
    try:
        labels = data.get("labels", [])
        values = data.get("values", [30, 40, 30])
        
        # Auto-generate labels if missing or mismatch
        if len(labels) != len(values):
            labels = [f"Item {i+1}" for i in range(len(values))]
            
        title = data.get("title", "Pie Chart")
        
        plt.style.use(CHART_STYLE)
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
        
        colors = plt.cm.Set3(range(len(labels)))
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=CHART_DPI, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pie chart generation failed: {str(e)}")

def generate_bar_chart(data: dict) -> str:
    """Generate bar chart and return base64 PNG"""
    try:
        categories = data.get("categories", ["Q1", "Q2", "Q3", "Q4"])
        values = data.get("values", [25, 40, 30, 45])
        title = data.get("title", "Bar Chart")
        xlabel = data.get("xlabel", "Category")
        ylabel = data.get("ylabel", "Value")
        
        plt.style.use(CHART_STYLE)
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
        
        bars = ax.bar(categories, values, color='steelblue', alpha=0.8)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=10)
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=CHART_DPI, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bar chart generation failed: {str(e)}")

def generate_line_chart(data: dict) -> str:
    """Generate line chart and return base64 PNG"""
    try:
        x_values = data.get("x_values", list(range(10)))
        y_values = data.get("y_values", [i**2 for i in range(10)])
        title = data.get("title", "Line Chart")
        xlabel = data.get("xlabel", "X Axis")
        ylabel = data.get("ylabel", "Y Axis")
        
        plt.style.use(CHART_STYLE)
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=CHART_DPI)
        
        ax.plot(x_values, y_values, color='crimson', linewidth=2, marker='o', markersize=6)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=CHART_DPI, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Line chart generation failed: {str(e)}")

# ============================================================
# MAIN TASK ENDPOINT
# ============================================================

@app.post("/execute_task", response_model=TaskResult)
async def execute_task(offer: JobOffer):
    """
    Execute chart generation task using A2A Protocol
    """
    start_time = datetime.now(timezone.utc)
    
    print("\n" + "="*60)
    print(f"📩 Received A2A Job Offer: {offer.job_id}")
    print(f"   👤 Buyer: {offer.buyer_id}")
    print(f"   💰 Budget Cap: ${offer.constraints.max_price}")
    print(f"   🏷️  My Price:  ${PRICE_PER_TASK}")
    
    # 1. CHECK CONSTRAINTS (The "Mail Sorter" Logic)
    if offer.constraints.max_price < PRICE_PER_TASK:
        print(f"   ❌ REJECTED: Budget too low (${offer.constraints.max_price} < ${PRICE_PER_TASK})")
        return TaskResult(
            status="rejected",
            result="",
            invoice=0.0,
            completed_at=datetime.now(timezone.utc).isoformat(),
            error=f"Budget constraint not met. My price: {PRICE_PER_TASK}, Max budget: {offer.constraints.max_price}"
        )
    
    print(f"   ✅ ACCEPTED: Budget sufficient")
    
    try:
        # Parse task data from payload
        task_data = offer.task_payload
        
        # Handle nested 'data' if present, or use payload directly
        # The PM sends { "data": [...], "instruction": ... }
        # But our chart logic expects specific keys. Let's adapt.
        
        chart_type = "pie" # Default
        chart_data = {}
        
        if "chart_type" in task_data:
            chart_type = task_data["chart_type"]
            chart_data = task_data.get("data", {})
        elif "data" in task_data:
             # Try to infer from generic payload
             chart_data = {"values": task_data["data"]}
             if "instruction" in task_data:
                 chart_data["title"] = task_data["instruction"]
        
        print(f"   Chart type: {chart_type}")
        print(f"   Data keys: {list(chart_data.keys())}")
        print("="*60)
        
        # Generate chart based on type
        print(f"🎨 Generating {chart_type} chart with matplotlib...")
        
        if chart_type == "pie":
            img_base64 = generate_pie_chart(chart_data)
        elif chart_type == "bar":
            img_base64 = generate_bar_chart(chart_data)
        elif chart_type == "line":
            img_base64 = generate_line_chart(chart_data)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported chart type: {chart_type}. Supported: pie, bar, line"
            )
        
        print(f"✅ Chart generated successfully ({len(img_base64)} bytes)")
        
        return TaskResult(
            status="done",
            result=img_base64,
            invoice=PRICE_PER_TASK,
            completed_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        print(f"❌ Chart generation failed: {str(e)}")
        return TaskResult(
            status="error",
            result=f"[ERROR] Chart generation failed: {str(e)}",
            invoice=0.0,
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
        "price": PRICE_PER_TASK,
        "chart_types": ["pie", "bar", "line"],
        "dpi": CHART_DPI
    }

@app.get("/.well-known/agent.json", response_model=AgentCard)
async def get_agent_card():
    """Return the public Agent Card (Passport)"""
    return AgentCard(
        protocol_version="AI_MARKETPLACE_v1",
        agent={
            "name": AGENT_NAME,
            "version": "1.0.0",
            "description": f"Budget-friendly chart generation ({CHART_DPI} DPI)",
            "vendor": "SanreAI",
            "homepage": f"http://127.0.0.1:{AGENT_PORT}"
        },
        capabilities=[
            {
                "type": CAPABILITY,
                "supported_chart_types": ["pie", "bar", "line"],
                "output_formats": ["png"]
            }
        ],
        pricing={
            "model": "fixed",
            "amount": PRICE_PER_TASK,
            "currency": "USD",
            "billing_unit": "per_chart"
        },
        performance={
            "avg_latency_ms": 500,
            "max_concurrent_jobs": 10
        },
        endpoints={
            "execute_task": f"http://127.0.0.1:{AGENT_PORT}/execute_task",
            "health": f"http://127.0.0.1:{AGENT_PORT}/health"
        },
        payment={
            "accepted_methods": ["escrow"],
            "wallet_address": "0x1234...abcd"
        }
    )
# ============================================================
# STARTUP: REGISTER WITH REGISTRY
# ============================================================

@app.on_event("startup")
async def startup_event():
    print(f"\n🤖 {AGENT_NAME} starting up...")
    print(f"🎨 Matplotlib configured (DPI: {CHART_DPI})")
    
    # Register with registry
    registration_data = {
        "name": AGENT_NAME,
        "capability": CAPABILITY,
        "url": f"http://127.0.0.1:{AGENT_PORT}/execute_task",  # ← Fixed
        "price": PRICE_PER_TASK,  # ← Fixed
        "description": f"Fast & cheap chart generation at {CHART_DPI} DPI"
    }	   
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📍 Attempting to register with registry at {REGISTRY_URL}")
            response = requests.post(
            f"{REGISTRY_URL}/register",  # ← Fixed
            json=registration_data,
            timeout=5
        )
            
            if response.status_code == 200:
                print(f"✅ Successfully registered with registry!")
                print(f"   Agent: {AGENT_NAME}")
                print(f"   Capability: {CAPABILITY}")
                print(f"   Price: ${PRICE_PER_TASK}")
                print(f"   Quality: {CHART_DPI} DPI (Premium)")
                break
            else:
                print(f"⚠️  Registration returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                print(f"⚠️  Attempt {attempt}/{max_retries}: Registry not reachable. Retrying in 2s...")
                import time
                time.sleep(2)
            else:
                print(f"❌ Failed to register after {max_retries} attempts. Agent will continue running but won't be discoverable.")

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🚀 Starting {AGENT_NAME} on http://127.0.0.1:{AGENT_PORT}")
    print(f"💼 Capability: {CAPABILITY}")
    print(f"💰 Price: ${PRICE_PER_TASK} (40% cheaper!)")
    print(f"🎨 Quality: {CHART_DPI} DPI (Budget)")
    print(f"📊 Chart Types: pie, bar, line")
    print(f"\n{'='*60}\n")
    
    uvicorn.run(app, host="127.0.0.1", port=AGENT_PORT)

