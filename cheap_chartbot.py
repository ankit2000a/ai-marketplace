"""
Cheap ChartBot - Lower price, lower quality
"""
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
import uvicorn
import asyncio
import time
from datetime import datetime, UTC

AGENT_NAME = "ChartBot_Budget_v1"
AGENT_URL = "http://127.0.0.1:8004"
AGENT_CAPABILITY = "generate_charts"
AGENT_PRICE = 0.03  # Cheaper!
REGISTRY_URL = "http://127.0.0.1:8000"

class TaskRequest(BaseModel):
    task_data: str

class TaskResponse(BaseModel):
    status: str
    result: str
    invoice: float
    completed_at: str

async def register_with_registry():
    print(f"🤖 {AGENT_NAME} starting up...")
    print(f"📍 Attempting to register with registry at {REGISTRY_URL}")
    
    registration_data = {
        "name": AGENT_NAME,
        "url": AGENT_URL,
        "capability": AGENT_CAPABILITY,
        "price": AGENT_PRICE
    }
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{REGISTRY_URL}/register",
                    json=registration_data
                )
                
                if response.status_code == 200:
                    print(f"✅ Successfully registered with registry!")
                    print(f"   Agent: {AGENT_NAME}")
                    print(f"   Capability: {AGENT_CAPABILITY}")
                    print(f"   Price: ${AGENT_PRICE} (cheaper than Pro!)")
                    return
                else:
                    print(f"⚠️  Registration failed with status {response.status_code}")
        
        except httpx.ConnectError:
            print(f"⚠️  Attempt {attempt}/{max_retries}: Registry not reachable. Retrying in {retry_delay}s...")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
        except Exception as e:
            print(f"❌ Error during registration: {e}")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
    
    print(f"❌ Failed to register after {max_retries} attempts.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_with_registry()
    yield
    print(f"👋 {AGENT_NAME} shutting down...")

app = FastAPI(title="Budget Chart Generation Agent", lifespan=lifespan)

@app.post("/execute_task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    print(f"📋 Received task: {request.task_data}")
    print(f"⚙️  Processing budget chart generation...")
    
    time.sleep(1.0)  # Slower than Pro (1.0s vs 0.5s)
    
    # Lower quality output
    chart_data = f"[LOW_QUALITY_CHART: {request.task_data.replace(' ', '_')}]"
    completed_at = datetime.now(UTC).isoformat()
    
    response = TaskResponse(
        status="done",
        result=chart_data,
        invoice=AGENT_PRICE,
        completed_at=completed_at
    )
    
    print(f"✅ Task completed! Invoice: ${AGENT_PRICE}")
    
    return response

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "agent": AGENT_NAME
    }

if __name__ == "__main__":
    print(f"🚀 Starting {AGENT_NAME} on {AGENT_URL}")
    uvicorn.run(app, host="127.0.0.1", port=8004)