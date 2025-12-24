#!/bin/bash

# Script to add dark: prefix to all color classes in dashboard pages
# This ensures proper light/dark mode support

PAGES=(
  "src/app/dashboard/analysis/page.tsx"
  "src/app/dashboard/insider/page.tsx"
  "src/app/dashboard/derivatives/page.tsx"
  "src/app/dashboard/screener/page.tsx"
)

for page in "${PAGES[@]}"; do
  echo "Processing $page..."
  
  # Common patterns to fix:
  # bg-slate-XXX -> bg-white dark:bg-slate-XXX (for cards/backgrounds)
  # text-white -> text-slate-900 dark:text-white
  # text-slate-400 -> text-slate-600 dark:text-slate-400
  # border-slate-800 -> border-slate-300 dark:border-slate-800
  
  # Note: This is a template - actual replacements need to be done carefully
  # to avoid breaking existing dark: prefixes
  
done

echo "Done! Please review changes before committing."
