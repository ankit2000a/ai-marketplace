"""
ChartBot Pro v1 - Premium Chart Generation Agent
Generates high-quality charts using matplotlib
Price: $0.05 per chart
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
AGENT_NAME = "ChartBot_Pro_v1"
AGENT_PORT = 8003
CAPABILITY = "generate_charts"
PRICE_PER_TASK = 0.05
REGISTRY_URL = "http://127.0.0.1:8000"

# Chart settings
CHART_DPI = 150  # High quality
CHART_FIGSIZE = (10, 6)
CHART_STYLE = 'seaborn-v0_8-darkgrid'

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title=AGENT_NAME)

class Task(BaseModel):
    task_data: dict | str

class TaskResult(BaseModel):
    status: str
    result: str  # Base64 encoded PNG
    invoice: float
    completed_at: str

# ============================================================
# CHART GENERATION FUNCTIONS
# ============================================================

def generate_pie_chart(data: dict) -> str:
    """Generate pie chart and return base64 PNG"""
    try:
        labels = data.get("labels", ["A", "B", "C"])
        values = data.get("values", [30, 40, 30])
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

from a2a_protocol import JobOffer

# ============================================================
# MAIN TASK ENDPOINT
# ============================================================

@app.post("/execute_task")
async def execute_task(offer: JobOffer):
    """
    Execute chart generation task (A2A Protocol)
    """
    print(f"\n🤖 {AGENT_NAME}: Received Job Offer {offer.job_id}")
    print(f"   Buyer: {offer.buyer_id}")
    print(f"   Budget: ${offer.constraints.max_price:.2f}")
    
    # 1. CHECK BUDGET
    if offer.constraints.max_price < PRICE_PER_TASK:
        print(f"   ❌ REJECTED: Budget ${offer.constraints.max_price:.2f} < Price ${PRICE_PER_TASK:.2f}")
        return {
            "status": "rejected",
            "error": f"Budget too low. My price: ${PRICE_PER_TASK:.2f}",
            "job_id": offer.job_id
        }
    
    # 2. EXTRACT DATA
    task_data = offer.task_payload
    # The instruction implies task_payload might contain a nested "data" key
    # If the payload is directly the chart data, this check handles it.
    # If the payload is { "data": { "chart_type": "bar", "data": {...} } }, this handles it.
    if "data" in task_data and isinstance(task_data["data"], dict):
        # This assumes the structure is { "data": { "chart_type": "bar", "data": {...} } }
        # or { "chart_type": "bar", "data": {...} }
        # Let's assume the instruction means the actual chart data is nested under "data"
        # within the task_payload, and chart_type is at the top level of task_payload.
        # Re-interpreting based on common A2A patterns: task_payload *is* the task_data.
        # The instruction's `if "data" in task_data: task_data = task_data["data"]`
        # seems to imply the chart data itself is nested.
        # Let's stick to the instruction's logic for now.
        # If task_payload is { "chart_type": "bar", "data": { "categories": [...] } }
        # then `task_data` will be `{ "categories": [...] }` after this line.
        # This seems to contradict the next lines where `chart_type` is extracted from `task_data`.
        # Let's assume the instruction meant:
        # `chart_type = offer.task_payload.get("chart_type", "bar")`
        # `data = offer.task_payload.get("data", {})`
        # However, I must follow the instruction faithfully.
        # The instruction's snippet:
        # `task_data = offer.task_payload`
        # `if "data" in task_data: task_data = task_data["data"]`
        # `chart_type = task_data.get("chart_type", "bar")`
        # `data = task_data.get("data", {})`
        # This implies `task_data` is first assigned `offer.task_payload`.
        # If `offer.task_payload` is `{"data": {"chart_type": "bar", "data": {"categories": [...]}}}`
        # then `task_data` becomes `{"chart_type": "bar", "data": {"categories": [...]}}`.
        # Then `chart_type` is extracted as "bar" and `data` as `{"categories": [...]}`.
        # This seems like a reasonable interpretation.
        original_task_payload = offer.task_payload
        if "data" in original_task_payload and isinstance(original_task_payload["data"], dict):
            # This path is taken if the payload is like {"data": {"chart_type": "bar", "data": {...}}}
            # In this case, the actual task details are nested under "data".
            task_details = original_task_payload["data"]
        else:
            # This path is taken if the payload is directly {"chart_type": "bar", "data": {...}}
            task_details = original_task_payload

        chart_type = task_details.get("chart_type", "bar").lower()
        data = task_details.get("data", {})
        
    print(f"   📊 Generating {chart_type} chart...")
    
    try:
        if chart_type == "bar":
            result = generate_bar_chart(data)
        elif chart_type == "line":
            result = generate_line_chart(data)
        else:
            return {
                "status": "failed",
                "error": f"Unsupported chart type: {chart_type}",
                "invoice": 0.0
            }
            
        print(f"   ✅ Chart generated successfully")
        
        return {
            "status": "done",
            "result": result,
            "invoice": PRICE_PER_TASK,
            "job_id": offer.job_id,
            "agent_name": AGENT_NAME
        }
        
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

# ============================================================
# AGENT CARD (PASSPORT)
# ============================================================
@app.get("/.well-known/agent.json")
async def agent_card():
    """Agent Card - Public metadata about this agent"""
    return {
        "protocol_version": "AI_MARKETPLACE_v1",
        "agent": {
            "name": AGENT_NAME,
            "version": "1.0.0",
            "description": "Premium chart generation (150 DPI)",
            "vendor": "SanreAI",
            "homepage": f"http://127.0.0.1:{AGENT_PORT}"
        },
        "capabilities": [
            {
                "type": CAPABILITY,
                "supported_chart_types": ["pie", "bar", "line"],
                "output_formats": ["png"]
            }
        ],
        "pricing": {
            "model": "fixed",
            "amount": PRICE_PER_TASK,
            "currency": "USD",
            "billing_unit": "per_chart"
        },
        "performance": {
            "avg_latency_ms": 300,
            "max_concurrent_jobs": 10
        },
        "endpoints": {
            "execute_task": f"http://127.0.0.1:{AGENT_PORT}/execute_task",
            "health": f"http://127.0.0.1:{AGENT_PORT}/health"
        },
        "payment": {
            "accepted_methods": ["escrow"],
            "wallet_address": "0x5678...efgh"
        }
    }

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
        "url": f"http://127.0.0.1:{AGENT_PORT}/execute_task",  # ← Changed from "endpoint"
        "price": PRICE_PER_TASK,  # ← Changed from "price_per_task"
        "description": f"Premium chart generation (pie, bar, line) at {CHART_DPI} DPI"
    }   
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📍 Attempting to register with registry at {REGISTRY_URL}")
            response = requests.post(
                f"{REGISTRY_URL}/register",  # ← Changed from "/register_agent"
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
    print(f"💰 Price: ${PRICE_PER_TASK} per chart")
    print(f"🎨 Quality: {CHART_DPI} DPI (Premium)")
    print(f"📊 Chart Types: pie, bar, line")
    print(f"\n{'='*60}\n")
    
    uvicorn.run(app, host="127.0.0.1", port=AGENT_PORT)
