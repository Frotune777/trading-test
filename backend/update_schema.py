import asyncio
import sys
import os
from sqlalchemy import text

# Ensure app can be imported
sys.path.append(os.getcwd())

from app.core.database import SessionLocal

async def main():
    print("🛠️  Updating database schema for Risk Metrics...")
    
    try:
        async with SessionLocal() as session:
            # List of columns to add
            columns = [
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS var_95_90d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS var_99_90d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS beta_30d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS beta_60d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS beta_252d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS sharpe_30d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS sharpe_60d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS sharpe_252d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS volatility_30d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS volatility_60d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS volatility_252d DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS beta DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS sharpe_ratio DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS volatility DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS volatility DECIMAL(10, 4);",
                "ALTER TABLE risk_metrics ADD COLUMN IF NOT EXISTS data_points_used INTEGER;",
                """
                CREATE TABLE IF NOT EXISTS quad_user_preferences (
                    user_id VARCHAR(50) PRIMARY KEY DEFAULT 'default',
                    weights JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
            
            for sql in columns:
                print(f"Executing: {sql}")
                await session.execute(text(sql))
            
            await session.commit()
            print("✅ Schema updated successfully.")
            
    except Exception as e:
        print(f"❌ Error updating schema: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
