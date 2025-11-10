#!/usr/bin/env python3
"""
Fix Streamlit deprecation warnings across all dashboard files
Replaces use_container_width with width parameter
"""

from pathlib import Path
import re

# Files to fix
DASHBOARD_FILES = [
    'dashboard/app.py',
    'dashboard/app_v3.py',
    'dashboard/app_v3_copy.py',
    'dashboard/pages/analytics.py',
    'dashboard/pages/data_manager.py',
    'dashboard/pages/models.py',
    'dashboard/pages/mtf_analysis.py',
    'dashboard/pages/portfolio.py',
    'dashboard/pages/research.py',
    'dashboard/pages/settings.py',
    'dashboard/pages/trading.py',
    'dashboard/components/charts.py',
    'dashboard/components/metrics.py',
    'dashboard/components/navigation.py',
    'dashboard/components/tables.py',
]

def fix_file(filepath: Path):
    """Fix a single file"""
    if not filepath.exists():
        print(f"⏭️  {filepath} - File not found, skipping")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Replace use_container_width=True with width='stretch'
    content = content.replace('use_container_width=True', "width='stretch'")
    
    # Replace use_container_width=False with width='content'
    content = content.replace('use_container_width=False', "width='content'")
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ {filepath} - Fixed")
        return True
    else:
        print(f"⏭️  {filepath} - No changes needed")
        return False

def main():
    print("="*60)
    print("🔧 Fixing Streamlit Deprecation Warnings")
    print("="*60)
    print()
    
    project_root = Path(__file__).parent
    fixed_count = 0
    
    for file_path in DASHBOARD_FILES:
        full_path = project_root / file_path
        if fix_file(full_path):
            fixed_count += 1
    
    print()
    print("="*60)
    print(f"✅ Complete! Fixed {fixed_count} files")
    print("="*60)

if __name__ == '__main__':
    main()