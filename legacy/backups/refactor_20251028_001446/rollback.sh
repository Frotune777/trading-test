#!/bin/bash
# Rollback script - Generated 2025-10-28 00:14:46

echo "🔄 Rolling back NSE refactoring..."

# Restore backed up files
cp "/home/fortune/Desktop/Python_Projects/fortune_trading/backups/refactor_20251028_001446/nse_complete.py" "/home/fortune/Desktop/Python_Projects/fortune_trading/data_sources/nse_complete.py"
cp "/home/fortune/Desktop/Python_Projects/fortune_trading/backups/refactor_20251028_001446/nse_utils.py" "/home/fortune/Desktop/Python_Projects/fortune_trading/external_libs/nse_utils.py"
cp "/home/fortune/Desktop/Python_Projects/fortune_trading/backups/refactor_20251028_001446/nse_master_data.py" "/home/fortune/Desktop/Python_Projects/fortune_trading/external_libs/nse_master_data.py"

echo "✅ Rollback complete!"
echo "⚠️  You may need to restore import statements manually"
