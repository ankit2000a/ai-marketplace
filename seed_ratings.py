from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from registry import AgentRecord, Base

DATABASE_URL = "sqlite:///./marketplace.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def update_rating(name, rating):
    agent = db.query(AgentRecord).filter(AgentRecord.name == name).first()
    if agent:
        agent.rating = rating
        db.commit()
        print(f"✅ Updated {name} rating to {rating}")
    else:
        print(f"❌ Agent {name} not found")

update_rating("ChartBot_Budget_v1", 3.5)
update_rating("ChartBot_Pro_v1", 5.0)
update_rating("TextSummarize_v1", 4.8)

db.close()
