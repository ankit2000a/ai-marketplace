"""
Registry Service - Agent Marketplace with scoring and ratings
Run on: http://127.0.0.1:8000

Features:
- Agents register with capability & price
- /search returns top N agents scored by price/quality/speed/reliability with buyer-adjustable weights
- /rate_transaction allows buyers to rate a completed transaction and updates agent metrics
- /report_transaction logs transactions
- For local dev, if DB schema changed, remove marketplace.db to recreate
"""
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional
import uvicorn

# ============================================================
# DATABASE SETUP
# ============================================================
DATABASE_URL = "sqlite:///./marketplace.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modern SQLAlchemy 2.0 Base
class Base(DeclarativeBase):
    pass

# ============================================================
# DATABASE MODELS
# ============================================================
class AgentRecord(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    capability = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Reputation / performance metrics
    rating = Column(Float, default=5.0)            # 1.0 - 5.0
    total_jobs = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.5) # seconds
    uptime_pct = Column(Float, default=100.0)      # percent
    total_earned = Column(Float, default=0.0)
    
    __table_args__ = (
        Index('idx_capability', 'capability'),
        Index('idx_name', 'name'),
    )
    
    @property
    def success_rate(self) -> float:
        if self.total_jobs == 0:
            return 100.0
        return (self.successful_jobs / self.total_jobs) * 100.0

class TransactionRecord(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, nullable=True)
    seller_name = Column(String, nullable=False)
    capability = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    success = Column(Boolean, default=True)  # New field
    completed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class FeedbackRecord(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    rating = Column(Float, nullable=False)  # 1.0 - 5.0
    feedback_text = Column(String, nullable=True)
    would_hire_again = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Create tables
Base.metadata.create_all(bind=engine)

# ============================================================
# PYDANTIC MODELS
# ============================================================
class AgentRegisterRequest(BaseModel):
    name: str
    url: str
    capability: str
    price: float = Field(gt=0, description="Price must be positive")

class AgentResponse(BaseModel):
    id: int
    name: str
    url: str
    capability: str
    price: float
    rating: float
    total_jobs: int
    success_rate: float
    avg_response_time: float
    
    class Config:
        from_attributes = True

class TransactionReportRequest(BaseModel):
    buyer_id: str
    seller_name: str
    amount: float = Field(ge=0, description="Transaction amount")
    success: bool = True  # New field

class TransactionResponse(BaseModel):
    id: int
    buyer_id: Optional[str]
    seller_name: str
    capability: str
    price: float
    success: bool
    completed_at: datetime
    
    class Config:
        from_attributes = True

class RateRequest(BaseModel):
    transaction_id: int
    rating: float = Field(ge=1.0, le=5.0, description="Rating between 1.0 and 5.0")
    feedback: Optional[str] = None
    would_hire_again: bool = True

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="Agent Marketplace Registry (scoring + ratings)")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def calculate_agent_score(agent: AgentRecord, max_price: float, max_resp_time: float, prefs: dict) -> float:
    """Calculate final score for an agent given buyer preferences"""
    # Normalize and bound between 0..1
    price_score = 1.0
    if max_price > 0:
        price_score = max(0.0, 1.0 - (agent.price / max_price))
    
    quality_score = max(0.0, min(1.0, (agent.rating or 5.0) / 5.0))
    
    speed_score = 1.0
    if max_resp_time > 0:
        speed_score = max(0.0, 1.0 - (agent.avg_response_time / max_resp_time))
    
    reliability_score = max(0.0, min(1.0, (agent.success_rate or 100.0) / 100.0))
    
    final = (
        price_score * prefs['price_weight'] +
        quality_score * prefs['quality_weight'] +
        speed_score * prefs['speed_weight'] +
        reliability_score * prefs['reliability_weight']
    )
    return final

# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/register", response_model=AgentResponse)
async def register_agent(request: AgentRegisterRequest):
    """Register or update an agent in the marketplace"""
    db = SessionLocal()
    try:
        existing_agent = db.query(AgentRecord).filter(AgentRecord.name == request.name).first()
        if existing_agent:
            # Update existing agent
            existing_agent.url = request.url
            existing_agent.capability = request.capability
            existing_agent.price = request.price
            existing_agent.registered_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_agent)
            print(f"✅ Agent updated: {request.name} ({request.capability}) - ${request.price}")
            return existing_agent
        else:
            # Create new agent
            new_agent = AgentRecord(
                name=request.name,
                url=request.url,
                capability=request.capability,
                price=request.price,
                registered_at=datetime.now(timezone.utc)
            )
            db.add(new_agent)
            db.commit()
            db.refresh(new_agent)
            print(f"✅ New agent registered: {request.name} ({request.capability}) - ${request.price}")
            return new_agent
    finally:
        db.close()

@app.get("/agents", response_model=List[AgentResponse])
async def get_all_agents():
    """Get list of all registered agents"""
    db = SessionLocal()
    try:
        agents = db.query(AgentRecord).all()
        return agents
    finally:
        db.close()

@app.post("/report_transaction")
async def report_transaction(report: TransactionReportRequest):
    """Report transaction with success/failure tracking"""
    db = SessionLocal()
    try:
        agent = db.query(AgentRecord).filter(AgentRecord.name == report.seller_name).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Create transaction record
        tr = TransactionRecord(
            buyer_id=report.buyer_id,
            seller_name=report.seller_name,
            capability=agent.capability,
            price=report.amount,
            success=report.success,  # NEW!
            completed_at=datetime.now(timezone.utc)
        )
        db.add(tr)
        
        # Update agent stats
        agent.total_jobs += 1
        
        if report.success:
            agent.successful_jobs += 1
            agent.total_earned += report.amount
        else:
            agent.failed_jobs += 1
            # Penalty: reduce rating
            agent.rating = max(1.0, agent.rating - 0.1)
        
        db.commit()
        db.refresh(tr)
        
        success_rate = (agent.successful_jobs / agent.total_jobs * 100) if agent.total_jobs > 0 else 100
        
        print(f"{'✅' if report.success else '❌'} Transaction: {report.buyer_id} → {report.seller_name}")
        print(f"   Success rate: {success_rate:.1f}% ({agent.successful_jobs}/{agent.total_jobs})")
        
        return {
            "status": "success",
            "agent_success_rate": success_rate,
            "transaction_id": tr.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log transaction: {str(e)}")
    finally:
        db.close()

@app.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions():
    """Get list of all transactions"""
    db = SessionLocal()
    try:
        rows = db.query(TransactionRecord).all()
        return rows
    finally:
        db.close()

@app.get("/search", response_model=List[AgentResponse])
async def search_agents(
    capability: str = Query(..., description="Capability to search for"),
    limit: int = Query(5, ge=1, le=20, description="Max number of candidate agents to return"),
    exclude: Optional[str] = Query(None, description="Comma-separated agent names to exclude"),
    price_weight: float = Query(0.3, ge=0.0, le=1.0),
    quality_weight: float = Query(0.4, ge=0.0, le=1.0),
    speed_weight: float = Query(0.2, ge=0.0, le=1.0),
    reliability_weight: float = Query(0.1, ge=0.0, le=1.0),
    max_price: Optional[float] = Query(None, description="Optional filter to cap price"),
    min_rating: Optional[float] = Query(None, description="Optional filter to require minimum rating")
):
    """
    Search for agents with a specific capability.
    Returns agents ranked by weighted score based on buyer preferences.
    """
    # Normalize weights to sum to 1.0
    total = price_weight + quality_weight + speed_weight + reliability_weight
    if total <= 0:
        raise HTTPException(status_code=400, detail="At least one weight must be > 0")
    
    prefs = {
        'price_weight': price_weight / total,
        'quality_weight': quality_weight / total,
        'speed_weight': speed_weight / total,
        'reliability_weight': reliability_weight / total
    }
    
    exclude_set = set(name.strip() for name in (exclude or "").split(",") if name.strip())
    
    db = SessionLocal()
    try:
        query = db.query(AgentRecord).filter(AgentRecord.capability == capability)
        
        if max_price is not None:
            query = query.filter(AgentRecord.price <= max_price)
        if min_rating is not None:
            query = query.filter(AgentRecord.rating >= min_rating)
        
        candidates = query.all()
        
        if not candidates:
            raise HTTPException(status_code=404, detail=f"No agents found with capability '{capability}'")
        
        # Compute normalization factors
        max_price_val = max((c.price for c in candidates), default=0.0)
        max_resp_time = max((c.avg_response_time for c in candidates), default=0.0)
        
        # Score each agent
        scored = []
        for c in candidates:
            if c.name in exclude_set:
                continue
            score = calculate_agent_score(c, max_price_val, max_resp_time, prefs)
            scored.append((c, score))
        
        # Sort by score descending (best first), then by price asc as tiebreaker
        scored.sort(key=lambda x: (-x[1], x[0].price))
        top = [t[0] for t in scored[:limit]]
        
        return top
    finally:
        db.close()

@app.post("/rate_transaction")
async def rate_transaction(rate: RateRequest):
    """
    Buyer posts a rating for a completed transaction.
    This updates the agent's aggregate rating and job counts.
    """
    db = SessionLocal()
    try:
        tx = db.query(TransactionRecord).filter(TransactionRecord.id == rate.transaction_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        agent = db.query(AgentRecord).filter(AgentRecord.name == tx.seller_name).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update feedback table
        fb = FeedbackRecord(
            transaction_id=rate.transaction_id,
            agent_name=agent.name,
            rating=rate.rating,
            feedback_text=rate.feedback,
            would_hire_again=rate.would_hire_again
        )
        db.add(fb)
        
        # Update agent aggregates
        prev_total = agent.total_jobs or 0
        prev_rating = agent.rating or 5.0
        agent.total_jobs = prev_total + 1
        
        # New average rating (weighted average)
        agent.rating = ((prev_rating * prev_total) + rate.rating) / agent.total_jobs
        
        # Update success/failure based on rating threshold
        if rate.rating >= 3.0:
            agent.successful_jobs = (agent.successful_jobs or 0) + 1
        else:
            agent.failed_jobs = (agent.failed_jobs or 0) + 1
        
        db.commit()
        
        print(f"⭐ Rating recorded: {agent.name} rated {rate.rating}/5.0 (new avg: {agent.rating:.2f})")
        
        return {
            "status": "success",
            "agent": agent.name,
            "new_rating": round(agent.rating, 2),
            "total_jobs": agent.total_jobs
        }
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "registry", "version": "2.0"}

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Registry Service")
    print("🌐 URL: http://127.0.0.1:8000")
    print("📊 Features:")
    print("   - Agent registration & discovery")
    print("   - Smart scoring (price, quality, speed, reliability)")
    print("   - Transaction tracking")
    print("   - Rating system")
    print("=" * 60)
    print()
    uvicorn.run(app, host="127.0.0.1", port=8000)