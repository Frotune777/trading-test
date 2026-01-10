from sqlalchemy import create_engine
from app.core.database import Base
from app.database.models_historical import OHLCVMetadata, MarketInsiderTrading, HistoricalOHLC, IndicatorHistory, MarketBulkDeal, MarketFIIDII

POSTGRES_URI_SYNC = "postgresql://postgres:postgres@localhost:5438/quad_trading"

def reset_tables():
    engine = create_engine(POSTGRES_URI_SYNC)
    print("Dropping existing metadata, market, and indicator tables...")
    OHLCVMetadata.__table__.drop(engine, checkfirst=True)
    MarketInsiderTrading.__table__.drop(engine, checkfirst=True)
    IndicatorHistory.__table__.drop(engine, checkfirst=True)
    
    print("Creating tables with updated schemas...")
    OHLCVMetadata.__table__.create(engine)
    MarketInsiderTrading.__table__.create(engine)
    IndicatorHistory.__table__.create(engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    reset_tables()
