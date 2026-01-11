"""
Company Data Population Script
Populates the companies table from NSE data sources
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.database.models_quad import Company
from app.data_sources.nse_utils import NseUtils
from app.data_sources.screener_enhanced import ScreenerEnhanced

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyDataPopulator:
    def __init__(self):
        self.nse = NseUtils()
        self.screener = ScreenerEnhanced()
        
    async def populate_companies(self, limit: int = None):
        """
        Populate companies table from NSE data
        
        Args:
            limit: Optional limit for testing (None = all companies)
        """
        async with SessionLocal() as db:
            try:
                logger.info("Fetching equity list from NSE...")
                
                # Get full equity list from NSE
                equity_df = self.nse.get_equity_full_list(list_only=False)
                logger.info(f"Found {len(equity_df)} companies from NSE")
                
                if limit:
                    equity_df = equity_df.head(limit)
                    logger.info(f"Limited to {limit} companies for testing")
                
                processed = 0
                skipped = 0
                errors = 0
                
                for idx, row in equity_df.iterrows():
                    symbol = row['SYMBOL']
                    name = row['NAME OF COMPANY']
                    series = row[' SERIES'].strip()
                    
                    # Skip non-EQ series (BE, BZ, etc.)
                    if series != 'EQ':
                        skipped += 1
                        continue
                    
                    try:
                        # Get additional company info from NSE
                        logger.info(f"Processing {symbol}...")
                        company_info = await self._get_company_info(symbol)
                        
                        if not company_info:
                            logger.warning(f"Could not fetch info for {symbol}, skipping")
                            skipped += 1
                            continue
                        
                        # Check if company already exists
                        stmt = select(Company).where(Company.symbol == symbol)
                        result = await db.execute(stmt)
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            # Update existing record
                            existing.name = name
                            existing.sector = company_info.get('sector')
                            existing.industry = company_info.get('industry')
                            existing.market_cap = company_info.get('market_cap')
                            existing.isin = company_info.get('isin')
                            existing.series = series
                            existing.listing_date = company_info.get('listing_date')
                            existing.last_updated = datetime.utcnow()
                            logger.info(f"Updated {symbol}")
                        else:
                            # Create new record
                            company = Company(
                                symbol=symbol,
                                name=name,
                                sector=company_info.get('sector'),
                                industry=company_info.get('industry'),
                                market_cap=company_info.get('market_cap'),
                                isin=company_info.get('isin'),
                                series=series,
                                listing_date=company_info.get('listing_date'),
                                data_source="NSE"
                            )
                            db.add(company)
                            logger.info(f"Created {symbol}")
                        
                        processed += 1
                        
                        # Commit every 10 records
                        if processed % 10 == 0:
                            await db.commit()
                            logger.info(f"Progress: {processed} processed, {skipped} skipped, {errors} errors")
                        
                        # Rate limiting to avoid NSE blocking
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        errors += 1
                        continue
                
                # Final commit
                await db.commit()
                
                logger.info("=" * 60)
                logger.info(f"Company data population complete!")
                logger.info(f"Processed: {processed}")
                logger.info(f"Skipped: {skipped}")
                logger.info(f"Errors: {errors}")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Fatal error in population: {e}")
                await db.rollback()
                raise
    
    async def _get_company_info(self, symbol: str) -> dict:
        """
        Get company information from NSE and Screener
        
        Returns dict with: sector, industry, market_cap, isin, listing_date
        """
        try:
            # Try NSE first
            equity_info = self.nse.equity_info(symbol)
            
            if not equity_info or 'error' in equity_info:
                return None
            
            # Extract basic info
            info = equity_info.get('info', {})
            metadata = equity_info.get('metadata', {})
            
            # Get sector/industry from metadata
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            isin = metadata.get('isin', '')
            
            # Try to get market cap from Screener (more reliable)
            market_cap = None
            try:
                screener_data = self.screener.get_company_data(symbol)
                if screener_data:
                    market_cap = screener_data.get('market_cap')
            except:
                pass
            
            # If no market cap from Screener, calculate from NSE data
            if not market_cap:
                price_info = equity_info.get('priceInfo', {})
                last_price = price_info.get('lastPrice', 0)
                
                # Get shares outstanding (if available)
                # This is a rough estimate - actual calculation would need more data
                market_cap = None  # Will be None if we can't calculate
            
            # Get listing date
            listing_date = None
            try:
                listing_date_str = metadata.get('listingDate')
                if listing_date_str:
                    listing_date = datetime.strptime(listing_date_str, '%d-%b-%Y')
            except:
                pass
            
            return {
                'sector': sector if sector != 'Unknown' else None,
                'industry': industry if industry != 'Unknown' else None,
                'market_cap': market_cap,
                'isin': isin,
                'listing_date': listing_date
            }
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    async def update_market_caps(self):
        """
        Update market caps for existing companies using latest price data
        """
        async with SessionLocal() as db:
            try:
                logger.info("Updating market caps...")
                
                # Get all companies without market cap
                stmt = select(Company).where(Company.market_cap.is_(None))
                result = await db.execute(stmt)
                companies = result.scalars().all()
                
                logger.info(f"Found {len(companies)} companies without market cap")
                
                updated = 0
                for company in companies:
                    try:
                        screener_data = self.screener.get_company_data(company.symbol)
                        if screener_data and screener_data.get('market_cap'):
                            company.market_cap = screener_data['market_cap']
                            company.last_updated = datetime.utcnow()
                            updated += 1
                            
                            if updated % 10 == 0:
                                await db.commit()
                                logger.info(f"Updated {updated} market caps")
                            
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Error updating market cap for {company.symbol}: {e}")
                        continue
                
                await db.commit()
                logger.info(f"Market cap update complete! Updated {updated} companies")
                
            except Exception as e:
                logger.error(f"Error updating market caps: {e}")
                await db.rollback()
                raise


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate companies table from NSE data')
    parser.add_argument('--limit', type=int, help='Limit number of companies (for testing)')
    parser.add_argument('--update-market-caps', action='store_true', help='Update market caps only')
    args = parser.parse_args()
    
    populator = CompanyDataPopulator()
    
    if args.update_market_caps:
        await populator.update_market_caps()
    else:
        await populator.populate_companies(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
