#!/usr/bin/env python3
"""
Fixed NSE Consolidation Script v2
Properly handles indentation when merging
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

project_root = Path.cwd()

print("=" * 70)
print("🔧 FIXED NSE CONSOLIDATION")
print("=" * 70)

# Check if source files exist
nse_utils_path = project_root / "external_libs/nse_utils.py"
nse_master_path = project_root / "external_libs/nse_master_data.py"

if not nse_utils_path.exists() or not nse_master_path.exists():
    print("❌ Source files not found")
    sys.exit(1)

print("\n📖 Reading source files...")
nse_utils_content = nse_utils_path.read_text(encoding='utf-8')
nse_master_content = nse_master_path.read_text(encoding='utf-8')

def extract_class_body(content: str, class_name: str) -> str:
    """Extract everything inside a class definition"""
    lines = content.split('\n')
    class_body_lines = []
    in_class = False
    class_indent = 0
    
    for i, line in enumerate(lines):
        # Find class definition
        if f'class {class_name}' in line:
            in_class = True
            # Determine base indentation
            class_indent = len(line) - len(line.lstrip())
            continue
        
        if in_class:
            # Check if we've exited the class (found another class or unindented code)
            if line.strip() and not line.startswith(' '):
                break
            
            # Check for another class at same level
            if line.strip().startswith('class ') and len(line) - len(line.lstrip()) == class_indent:
                break
            
            # Add the line (will be re-indented later)
            class_body_lines.append(line)
    
    return '\n'.join(class_body_lines)

def normalize_indentation(code: str, target_indent: int = 4) -> list:
    """Normalize code indentation to target level"""
    lines = code.split('\n')
    if not lines:
        return []
    
    # Find minimum indentation (excluding empty lines)
    min_indent = float('inf')
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)
    
    if min_indent == float('inf'):
        min_indent = 0
    
    # Normalize all lines
    normalized = []
    for line in lines:
        if line.strip():
            # Remove minimum indent and add target indent
            current_indent = len(line) - len(line.lstrip())
            relative_indent = current_indent - min_indent
            new_line = ' ' * (target_indent + relative_indent) + line.lstrip()
            normalized.append(new_line)
        else:
            normalized.append('')
    
    return normalized

# Extract imports from nse_utils.py
print("📦 Extracting imports...")
import_lines = []
for line in nse_utils_content.split('\n'):
    stripped = line.strip()
    if stripped.startswith('import ') or stripped.startswith('from '):
        # Skip internal imports
        if 'nse_utils' not in line and 'nse_master' not in line:
            import_lines.append(line)
    elif stripped.startswith('class '):
        break

# Build the output
output = []

# Header
output.append('"""')
output.append('Complete NSE Data Source - Consolidated')
output.append('')
output.append('Combines NseUtils + NSEMasterData classes')
output.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
output.append('"""')
output.append('')

# Imports
output.extend(import_lines)
output.append('')
output.append('from data_sources.base_source import DataSource')
output.append('from typing import Dict, Any, List, Optional')
output.append('')
output.append('')

# Class definition
output.append('class NSEComplete(DataSource):')
output.append('    """')
output.append('    Complete NSE data source combining:')
output.append('    - NseUtils: NSE API methods')
output.append('    - NSEMasterData: Symbol search and master data')
output.append('    """')
output.append('')

# Extract and merge class bodies
print("🔄 Extracting NseUtils class body...")
nse_utils_body = extract_class_body(nse_utils_content, 'NseUtils')
utils_lines = normalize_indentation(nse_utils_body, target_indent=4)

print("🔄 Extracting NSEMasterData class body...")
nse_master_body = extract_class_body(nse_master_content, 'NSEMasterData')
master_lines = normalize_indentation(nse_master_body, target_indent=4)

# Fix __init__ to call super().__init__
print("🔧 Fixing __init__ method...")
fixed_init = []
in_init = False
for line in utils_lines:
    if 'def __init__(self)' in line:
        in_init = True
        fixed_init.append('    def __init__(self):')
        fixed_init.append('        super().__init__("NSE Complete")')
        continue
    
    if in_init:
        # Skip until next method
        if line.strip().startswith('def ') and '__init__' not in line:
            in_init = False
            fixed_init.append(line)
        elif not in_init:
            fixed_init.append(line)
        # If still in __init__, keep original lines
        else:
            fixed_init.append(line)
    else:
        fixed_init.append(line)

# Add NseUtils methods
output.append('    # ===== Methods from NseUtils =====')
output.append('')
output.extend(fixed_init)

# Add separator
output.append('')
output.append('    # ===== Methods from NSEMasterData =====')
output.append('')

# Add NSEMasterData methods (skip __init__)
skip_init = False
for line in master_lines:
    if 'def __init__' in line:
        skip_init = True
        continue
    
    if skip_init and line.strip().startswith('def '):
        skip_init = False
    
    if not skip_init:
        output.append(line)

# Add convenience method
output.append('')
output.append('    # ===== Convenience methods =====')
output.append('')
output.append('    def get_complete_data(self, symbol: str) -> Dict[str, Any]:')
output.append('        """Get all available data for a symbol"""')
output.append('        try:')
output.append('            return {')
output.append('                "symbol": symbol,')
output.append('                "company_info": self.equity_info(symbol),')
output.append('                "price_data": self.price_info(symbol),')
output.append('            }')
output.append('        except Exception as e:')
output.append('            self.logger.error(f"Error getting complete data: {e}")')
output.append('            return {}')
output.append('')

# Write file
output_path = project_root / "data_sources/nse_complete.py"
output_content = '\n'.join(output)

print(f"\n💾 Writing to {output_path.name}...")
output_path.write_text(output_content, encoding='utf-8')

print(f"   Lines: {len(output):,}")
print(f"   Size: {len(output_content):,} bytes")

# Validate syntax
print("\n🔍 Validating syntax...")
import ast
try:
    ast.parse(output_content)
    print("✅ Syntax validation PASSED")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
    print(f"\nContext:")
    lines = output_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    for i in range(start, end):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1:4d}: {lines[i]}")
    
    # Save debug file
    debug_path = project_root / "data_sources/nse_complete_DEBUG.py"
    debug_path.write_text(output_content, encoding='utf-8')
    print(f"\n💾 Saved debug file: {debug_path}")
    sys.exit(1)

# Test import
print("\n🧪 Testing import...")
try:
    # Clear any cached imports
    for mod in list(sys.modules.keys()):
        if 'nse_complete' in mod:
            del sys.modules[mod]
    
    sys.path.insert(0, str(project_root))
    from data_sources.nse_complete import NSEComplete
    
    print("✅ Import successful")
    
    # Try to instantiate
    nse = NSEComplete()
    print(f"✅ Instantiation successful: {nse.name}")
    
    # Check key methods
    key_methods = [
        'equity_info',
        'price_info', 
        'get_option_chain',
        'get_corporate_action',
        'search',
        'get_history'
    ]
    
    print("\n📋 Checking methods:")
    found = 0
    for method in key_methods:
        if hasattr(nse, method):
            print(f"  ✅ {method}")
            found += 1
        else:
            print(f"  ❌ {method}")
    
    print(f"\nMethods found: {found}/{len(key_methods)}")
    
    if found == len(key_methods):
        print("\n" + "=" * 70)
        print("✅ ✅ ✅  SUCCESS!  ✅ ✅ ✅")
        print("=" * 70)
        print("\nConsolidation complete. You can now:")
        print("1. Delete external_libs/nse_utils.py")
        print("2. Delete external_libs/nse_master_data.py")
        print("3. Run: python quick_validate.py")
    else:
        print("\n⚠️  Some methods missing - review the output")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)