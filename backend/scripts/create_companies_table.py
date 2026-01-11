"""
Simple script to create companies table and add sample data for testing
"""
import asyncio
import sys
sys.path.insert(0, '/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend')

from sqlalchemy import text
from app.core.database import async_engine, async_session_maker
from app.database.models_quad import Base, Company
from datetime import datetime

async def create_table_and_sample_data():
    """Create companies table and add sample data"""
    
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Companies table created")
    
    # Add sample data for testing
    sample_companies = [
        {
            "symbol": "RELIANCE",
            "name": "Reliance Industries Ltd",
            "sector": "Energy",
            "industry": "Refineries",
            "market_cap": 1800000.0,  # 18 lakh crores
        },
        {
            "symbol": "ONGC",
            "name": "Oil and Natural Gas Corporation Ltd",
            "sector": "Energy",
            "industry": "Oil Exploration",
            "market_cap": 350000.0,
        },
        {
            "symbol": "BPCL",
            "name": "Bharat Petroleum Corporation Ltd",
            "sector": "Energy",
            "industry": "Refineries",
            "market_cap": 120000.0,
        },
        {
            "symbol": "IOC",
            "name": "Indian Oil Corporation Ltd",
            "sector": "Energy",
            "industry": "Refineries",
            "market_cap": 140000.0,
        },
        {
            "symbol": "TCS",
            "name": "Tata Consultancy Services Ltd",
            "sector": "Information Technology",
            "industry": "IT Services",
            "market_cap": 1400000.0,
        },
        {
            "symbol": "INFY",
            "name": "Infosys Ltd",
            "sector": "Information Technology",
            "industry": "IT Services",
            "market_cap": 700000.0,
        },
    ]
    
    async with async_session_maker() as db:
        for comp_data in sample_companies:
            company = Company(**comp_data, data_source="Manual", series="EQ")
            db.add(company)
        
        await db.commit()
    
    print(f"✅ Added {len(sample_companies)} sample companies")
    print("\nSample companies:")
    for comp in sample_companies:
        print(f"  - {comp['symbol']}: {comp['name']} ({comp['sector']})")

if __name__ == "__main__":
    asyncio.run(create_table_and_sample_data())
