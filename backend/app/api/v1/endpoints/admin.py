"""
Admin API Endpoints for Database Management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from app.core.database import get_db, async_engine
from app.database.models_quad import Base, Company
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/create-companies-table")
async def create_companies_table(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Create companies table and populate with sample data
    """
    try:
        # Create all tables defined in models
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Add sample data
        sample_companies = [
            Company(symbol="RELIANCE", name="Reliance Industries Ltd", sector="Energy", 
                   industry="Refineries", market_cap=1800000.0, series="EQ", data_source="Manual"),
            Company(symbol="ONGC", name="Oil and Natural Gas Corporation Ltd", sector="Energy",
                   industry="Oil Exploration", market_cap=350000.0, series="EQ", data_source="Manual"),
            Company(symbol="BPCL", name="Bharat Petroleum Corporation Ltd", sector="Energy",
                   industry="Refineries", market_cap=120000.0, series="EQ", data_source="Manual"),
            Company(symbol="IOC", name="Indian Oil Corporation Ltd", sector="Energy",
                   industry="Refineries", market_cap=140000.0, series="EQ", data_source="Manual"),
            Company(symbol="GAIL", name="GAIL (India) Ltd", sector="Energy",
                   industry="Gas Distribution", market_cap=95000.0, series="EQ", data_source="Manual"),
            Company(symbol="TCS", name="Tata Consultancy Services Ltd", sector="Information Technology",
                   industry="IT Services", market_cap=1400000.0, series="EQ", data_source="Manual"),
            Company(symbol="INFY", name="Infosys Ltd", sector="Information Technology",
                   industry="IT Services", market_cap=700000.0, series="EQ", data_source="Manual"),
            Company(symbol="WIPRO", name="Wipro Ltd", sector="Information Technology",
                   industry="IT Services", market_cap=280000.0, series="EQ", data_source="Manual"),
            Company(symbol="HCLTECH", name="HCL Technologies Ltd", sector="Information Technology",
                   industry="IT Services", market_cap=380000.0, series="EQ", data_source="Manual"),
            Company(symbol="TECHM", name="Tech Mahindra Ltd", sector="Information Technology",
                   industry="IT Services", market_cap=120000.0, series="EQ", data_source="Manual"),
        ]
        
        for company in sample_companies:
            # Check if exists
            result = await db.execute(
                text("SELECT id FROM companies WHERE symbol = :symbol"),
                {"symbol": company.symbol}
            )
            if not result.scalar_one_or_none():
                db.add(company)
        
        await db.commit()
        
        # Get count
        result = await db.execute(text("SELECT COUNT(*) FROM companies"))
        count = result.scalar()
        
        return {
            "status": "success",
            "message": f"Companies table created and populated with {count} companies",
            "companies_added": len(sample_companies)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating table: {str(e)}")

@router.get("/companies/list")
async def list_companies(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """List all companies in the database"""
    try:
        result = await db.execute(
            text("SELECT symbol, name, sector, market_cap FROM companies ORDER BY sector, symbol")
        )
        companies = []
        for row in result:
            companies.append({
                "symbol": row[0],
                "name": row[1],
                "sector": row[2],
                "market_cap": float(row[3]) if row[3] else 0.0
            })
        
        return {
            "total": len(companies),
            "companies": companies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing companies: {str(e)}")
