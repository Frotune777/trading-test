#!/usr/bin/env python3
"""
Script to add dark: prefix to Tailwind color classes for light/dark mode support.
This ensures proper contrast in both themes.
"""

import re
import sys

def add_dark_prefix(content):
    """Add dark: prefix to color classes that don't have it."""
    
    # Patterns to update (background colors)
    replacements = [
        # Cards and backgrounds
        (r'className="([^"]*?)bg-slate-900([^"]*?)"', r'className="\1bg-white dark:bg-slate-900\2"'),
        (r'className="([^"]*?)bg-slate-950([^"]*?)"', r'className="\1bg-slate-50 dark:bg-slate-950\2"'),
        (r'className="([^"]*?)bg-slate-800([^"]*?)"', r'className="\1bg-slate-200 dark:bg-slate-800\2"'),
        
        # Text colors
        (r'className="([^"]*?)text-white([^"]*?)"', r'className="\1text-slate-900 dark:text-white\2"'),
        (r'className="([^"]*?)text-slate-400([^"]*?)"', r'className="\1text-slate-600 dark:text-slate-400\2"'),
        (r'className="([^"]*?)text-slate-500([^"]*?)"', r'className="\1text-slate-700 dark:text-slate-500\2"'),
        
        # Borders
        (r'className="([^"]*?)border-slate-800([^"]*?)"', r'className="\1border-slate-300 dark:border-slate-800\2"'),
        (r'className="([^"]*?)border-slate-700([^"]*?)"', r'className="\1border-slate-300 dark:border-slate-700\2"'),
    ]
    
    for pattern, replacement in replacements:
        # Only replace if 'dark:' is not already present in the className
        content = re.sub(pattern, lambda m: replacement if 'dark:' not in m.group(0) else m.group(0), content)
    
    return content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_dark_mode.py <file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    updated_content = add_dark_prefix(content)
    
    with open(filepath, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {filepath}")
