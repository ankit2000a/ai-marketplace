"""
Text Summarization Agent - REAL AI powered by Google Gemini
Port: 8002
Capability: summarize_text
Price: $0.02
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
import uvicorn
import asyncio
import os
from datetime import datetime, UTC
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
AGENT_NAME = "TextSummarize_v1"
AGENT_PORT = 8002  # ← Was missing!
AGENT_CAPABILITY = "summarize_text"
PRICE_PER_TASK = 0.02  # ← Changed from AGENT_PRICE
REGISTRY_URL = "http://127.0.0.1:8000"

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment variables!")
    print("   Create a .env file with: GEMINI_API_KEY=your_key_here")
    exit(1)

genai.configure(api_key=api_key)

# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================
class TaskRequest(BaseModel):
    task_data: str

class TaskResponse(BaseModel):
    status: str
    result: str
    invoice: float
    completed_at: str

# ============================================================
# REGISTRATION FUNCTION
# ============================================================
async def register_with_registry():
    print(f"🤖 {AGENT_NAME} starting up...")
    print(f"🔑 Gemini API configured (using REAL AI)")
    print(f"📍 Attempting to register with registry at {REGISTRY_URL}")
    
    registration_data = {
        "name": AGENT_NAME,
        "capability": AGENT_CAPABILITY,
        "url": f"http://127.0.0.1:{AGENT_PORT}/execute_task",
        "price": PRICE_PER_TASK,
        "description": "AI-powered text summarization using Google Gemini"
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
                    print(f"   URL: http://127.0.0.1:{AGENT_PORT}/execute_task")
                    print(f"   Price: ${PRICE_PER_TASK}")
                    print(f"   🎯 NOW USING REAL GEMINI AI")
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
    
    print(f"❌ Failed to register after {max_retries} attempts. Agent will continue running but won't be discoverable.")

# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_with_registry()
    yield
    print(f"👋 {AGENT_NAME} shutting down...")

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="AI Text Summarization Agent (Gemini-powered)", lifespan=lifespan)

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
            "description": "AI-powered text summarization using Google Gemini",
            "vendor": "SanreAI",
            "homepage": f"http://127.0.0.1:{AGENT_PORT}"
        },
        "capabilities": [
            {
                "type": AGENT_CAPABILITY,
                "max_input_length": 10000,
                "output_formats": ["text"]
            }
        ],
        "pricing": {
            "model": "fixed",
            "amount": PRICE_PER_TASK,
            "currency": "USD",
            "billing_unit": "per_summary"
        },
        "performance": {
            "avg_latency_ms": 800,
            "max_concurrent_jobs": 5
        },
        "endpoints": {
            "execute_task": f"http://127.0.0.1:{AGENT_PORT}/execute_task",
            "health": f"http://127.0.0.1:{AGENT_PORT}/health"
        },
        "payment": {
            "accepted_methods": ["escrow"],
            "wallet_address": "0x9abc...ijkl"
        }
    }



# ============================================================
# MAIN ENDPOINT
# ============================================================
from a2a_protocol import JobOffer

# ============================================================
@app.post("/execute_task")
async def execute_task(offer: JobOffer):
    """
    Execute text summarization task (A2A Protocol)
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
    task_payload = offer.task_payload
    if "data" in task_payload:
        text_to_summarize = task_payload["data"]
    else:
        # Fallback if payload is flat
        text_to_summarize = str(task_payload)
        
    print(f"   Input length: {len(text_to_summarize)} characters")
    
    try:
        # Use Gemini AI for real summarization
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Create prompt
        prompt = f"Provide a concise summary (2-3 sentences max) of the following text:\n\n{text_to_summarize}"
        
        print(f"🤖 Calling Gemini AI...")
        
        # Generate summary
        response = model.generate_content(prompt)
        
        if not response.text:
            raise Exception("Gemini returned empty response")
        
        summary_text = response.text.strip()
        
        print(f"✅ Summary generated successfully!")
        print(f"   Output length: {len(summary_text)} characters")
        print(f"   Invoice: ${PRICE_PER_TASK}")
        
        return {
            "status": "done",
            "result": summary_text,
            "invoice": PRICE_PER_TASK,
            "job_id": offer.job_id,
            "agent_name": AGENT_NAME
        }
        
    except Exception as e:
        error_msg = f"Summarization failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        return {
            "status": "failed",
            "error": error_msg,
            "invoice": 0.0
        }

# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "agent": AGENT_NAME,
        "capability": AGENT_CAPABILITY,
        "price": PRICE_PER_TASK,  # ← Fixed variable name
        "ai_provider": "Google Gemini",
        "version": "2.0-real-ai"
    }

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🚀 Starting {AGENT_NAME}")
    print(f"🌐 URL: http://127.0.0.1:{AGENT_PORT}")
    print(f"💼 Capability: {AGENT_CAPABILITY}")
    print(f"💰 Price: ${PRICE_PER_TASK} per task")
    print(f"🤖 AI Provider: Google Gemini")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host="127.0.0.1", port=AGENT_PORT)