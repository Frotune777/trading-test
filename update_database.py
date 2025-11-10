"""
Database Update CLI Tool
Offline-ready stock data updater
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.updater import DataUpdater
from database.db_manager import DatabaseManager
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Update stock database with latest data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update single stock
  python update_database.py TCS
  
  # Update multiple stocks
  python update_database.py TCS INFY WIPRO
  
  # Update all IT sector stocks
  python update_database.py --sector "Information Technology"
  
  # Update stale stocks (not updated in 24h)
  python update_database.py --stale 24
  
  # Force update even if recent
  python update_database.py TCS --force
  
  # Show database status
  python update_database.py --status
        """
    )
    
    parser.add_argument(
        'symbols',
        nargs='*',
        help='Stock symbols to update (e.g., TCS INFY WIPRO)'
    )
    
    parser.add_argument(
        '--sector',
        help='Update all stocks in a sector'
    )
    
    parser.add_argument(
        '--stale',
        type=int,
        metavar='HOURS',
        help='Update stocks not updated in X hours'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if recently updated'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show database status'
    )
    
    parser.add_argument(
        '--list-sectors',
        action='store_true',
        help='List all available sectors'
    )
    
    parser.add_argument(
        '--db',
        default='stock_data.db',
        help='Database path (default: stock_data.db)'
    )
    
    args = parser.parse_args()
    
    # Initialize
    updater = DataUpdater(db_path=args.db)
    
    # Handle different commands
    if args.status:
        show_status(updater)
    
    elif args.list_sectors:
        list_sectors(updater)
    
    elif args.sector:
        updater.update_sector(args.sector, force=args.force)
    
    elif args.stale:
        updater.update_stale_stocks(hours=args.stale)
    
    elif args.symbols:
        if len(args.symbols) == 1:
            # Single stock
            result = updater.update_stock(args.symbols[0], force=args.force)
            print_result(result)
        else:
            # Multiple stocks
            updater.update_multiple(args.symbols, force=args.force)
    
    else:
        # No arguments - show help
        parser.print_help()


def show_status(updater: DataUpdater):
    """Show database status."""
    status = updater.get_update_status()
    
    print(f"\n{'='*80}")
    print("📊 DATABASE STATUS")
    print(f"{'='*80}\n")
    
    # Database stats
    stats = status['database_stats']
    print(f"Database Size: {stats['database_size']:.2f} MB")
    print(f"Total Companies: {status['total_companies']}")
    print(f"Needs Update (24h): {status['needs_update_24h']}")
    
    print(f"\n📋 Table Record Counts:")
    for table, count in stats['table_counts'].items():
        if count > 0:
            print(f"  • {table:25s} {count:>8,} records")
    
    # Recent updates
    summary = status['update_summary']
    if summary:
        print(f"\n🔄 Recent Updates:")
        for item in summary[:10]:  # Show last 10
            print(f"  • {item['symbol']:10s} {item['table_name']:20s} {item['last_update']}")
    
    print(f"\n{'='*80}\n")


def list_sectors(updater: DataUpdater):
    """List all sectors."""
    sectors = updater.db.get_sectors()
    
    print(f"\n{'='*80}")
    print("📊 AVAILABLE SECTORS")
    print(f"{'='*80}\n")
    
    for sector in sectors:
        companies = updater.db.get_all_companies(sector=sector)
        print(f"  • {sector:50s} ({len(companies)} companies)")
    
    print(f"\n{'='*80}\n")


def print_result(result: dict):
    """Print single stock update result."""
    print(f"\n{'='*80}")
    print(f"UPDATE RESULT: {result['symbol']}")
    print(f"{'='*80}\n")
    
    if result.get('skipped'):
        print(f"⏭️  SKIPPED: {result.get('message')}")
        print(f"Last Update: {result.get('last_update')}")
    
    elif result.get('success'):
        print(f"✅ SUCCESS")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s\n")
        
        print("Updates:")
        for section, status in result['updates'].items():
            icon = '✅' if 'success' in status else '❌'
            print(f"  {icon} {section:25s} {status}")
    
    else:
        print(f"❌ FAILED\n")
        print("Errors:")
        for error in result.get('errors', []):
            print(f"  • {error}")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()