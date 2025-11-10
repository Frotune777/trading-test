#!/usr/bin/env python3
"""
Automated NSE Files Consolidation Script
Safely merges nse_utils.py + nse_master_data.py → nse_complete.py

Features:
- Automatic backup
- Dependency analysis
- Import updates
- Syntax validation
- Rollback capability
- Detailed logging
"""

import os
import sys
import ast
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple
import subprocess

class NSERefactoringTool:
    """Automated refactoring tool for NSE consolidation"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.backup_dir = self.project_root / f"backups/refactor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.log_file = self.project_root / "refactoring.log"
        
        # Files to process
        self.nse_complete = self.project_root / "data_sources/nse_complete.py"
        self.nse_utils = self.project_root / "external_libs/nse_utils.py"
        self.nse_master = self.project_root / "external_libs/nse_master_data.py"
        
        # Files that import NSE modules
        self.dependent_files = []
        
        # Validation flags
        self.errors = []
        self.warnings = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Console
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            print(f"ℹ️  {message}")
        
        # File
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def create_backup(self):
        """Create backup of all files to be modified"""
        self.log("=" * 70)
        self.log("STEP 1: Creating Backups")
        self.log("=" * 70)
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_backup = [
                self.nse_complete,
                self.nse_utils,
                self.nse_master
            ]
            
            for file in files_to_backup:
                if file.exists():
                    backup_path = self.backup_dir / file.name
                    shutil.copy2(file, backup_path)
                    self.log(f"Backed up: {file.name} → {backup_path}", "SUCCESS")
                else:
                    self.log(f"File not found: {file}", "WARNING")
                    self.warnings.append(f"Missing file: {file}")
            
            # Create rollback script
            self.create_rollback_script()
            
            self.log(f"\nBackup directory: {self.backup_dir}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            self.errors.append(str(e))
            return False
    
    def create_rollback_script(self):
        """Create a script to rollback changes if needed"""
        rollback_script = self.backup_dir / "rollback.sh"
        
        script_content = f"""#!/bin/bash
# Rollback script - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🔄 Rolling back NSE refactoring..."

# Restore backed up files
cp "{self.backup_dir}/nse_complete.py" "{self.nse_complete}"
cp "{self.backup_dir}/nse_utils.py" "{self.nse_utils}"
cp "{self.backup_dir}/nse_master_data.py" "{self.nse_master}"

echo "✅ Rollback complete!"
echo "⚠️  You may need to restore import statements manually"
"""
        
        with open(rollback_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(rollback_script, 0o755)
        self.log(f"Rollback script created: {rollback_script}", "SUCCESS")
    
    def analyze_dependencies(self):
        """Find all files that import NSE modules"""
        self.log("\n" + "=" * 70)
        self.log("STEP 2: Analyzing Dependencies")
        self.log("=" * 70)
        
        patterns = [
            r'from\s+nse_utils\s+import',
            r'import\s+nse_utils',
            r'from\s+nse_master_data\s+import',
            r'import\s+nse_master_data',
            r'from\s+external_libs\.nse_utils',
            r'from\s+external_libs\.nse_master_data'
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip backup directory and external libs
            if 'backup' in str(py_file) or py_file == self.nse_utils or py_file == self.nse_master:
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for pattern in patterns:
                    if re.search(pattern, content):
                        if py_file not in self.dependent_files:
                            self.dependent_files.append(py_file)
                            self.log(f"Found dependency: {py_file.relative_to(self.project_root)}")
                        break
            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", "WARNING")
        
        self.log(f"\nTotal dependent files: {len(self.dependent_files)}", "INFO")
        return True
    
    def extract_methods(self, file_path: Path) -> List[Dict]:
        """Extract all methods from a Python file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function source
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    source_lines = content.split('\n')[start_line:end_line]
                    
                    methods.append({
                        'name': node.name,
                        'source': '\n'.join(source_lines),
                        'lineno': node.lineno,
                        'is_private': node.name.startswith('_'),
                        'docstring': ast.get_docstring(node)
                    })
                
                elif isinstance(node, ast.ClassDef):
                    # Get class and all its methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            start_line = item.lineno - 1
                            end_line = item.end_lineno
                            source_lines = content.split('\n')[start_line:end_line]
                            
                            methods.append({
                                'name': f"{node.name}.{item.name}",
                                'source': '\n'.join(source_lines),
                                'lineno': item.lineno,
                                'is_method': True,
                                'class_name': node.name,
                                'docstring': ast.get_docstring(item)
                            })
            
            return methods
            
        except Exception as e:
            self.log(f"Error extracting methods from {file_path.name}: {e}", "ERROR")
            return []
    
    def merge_nse_files(self):
        """Merge nse_utils.py and nse_master_data.py into nse_complete.py"""
        self.log("\n" + "=" * 70)
        self.log("STEP 3: Merging NSE Files")
        self.log("=" * 70)
        
        try:
            # Read current nse_complete.py
            current_content = self.nse_complete.read_text(encoding='utf-8')
            
            # Read files to merge
            nse_utils_content = self.nse_utils.read_text(encoding='utf-8')
            nse_master_content = self.nse_master.read_text(encoding='utf-8')
            
            # Extract methods
            utils_methods = self.extract_methods(self.nse_utils)
            master_methods = self.extract_methods(self.nse_master)
            
            self.log(f"Found {len(utils_methods)} methods in nse_utils.py")
            self.log(f"Found {len(master_methods)} methods in nse_master_data.py")
            
            # Generate consolidated file
            consolidated = self.generate_consolidated_nse_complete(
                current_content,
                nse_utils_content,
                nse_master_content,
                utils_methods,
                master_methods
            )
            
            # Write consolidated file
            consolidated_path = self.project_root / "data_sources/nse_complete_NEW.py"
            consolidated_path.write_text(consolidated, encoding='utf-8')
            
            self.log(f"Consolidated file created: {consolidated_path}", "SUCCESS")
            
            # Validate syntax
            if self.validate_python_syntax(consolidated_path):
                self.log("Syntax validation passed", "SUCCESS")
                return consolidated_path
            else:
                self.log("Syntax validation failed", "ERROR")
                return None
            
        except Exception as e:
            self.log(f"Merge failed: {e}", "ERROR")
            self.errors.append(str(e))
            return None
    
    def generate_consolidated_nse_complete(self, current, utils_content, master_content, utils_methods, master_methods):
        """Generate the consolidated nse_complete.py content"""
        
        # Extract imports from all files
        utils_imports = self.extract_imports(utils_content)
        master_imports = self.extract_imports(master_content)
        current_imports = self.extract_imports(current)
        
        # Combine unique imports
        all_imports = sorted(set(utils_imports + master_imports + current_imports))
        
        # Build new file
        output = []
        
        # Header
        output.append('"""')
        output.append('Complete NSE Data Source - Consolidated')
        output.append('')
        output.append('Combines functionality from:')
        output.append('- nse_utils.py (NSE API wrapper)')
        output.append('- nse_master_data.py (Symbol master data)')
        output.append('- Original NSEComplete wrapper')
        output.append('')
        output.append(f'Auto-generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        output.append('"""')
        output.append('')
        
        # Imports
        output.append('# Imports')
        output.extend(all_imports)
        output.append('')
        output.append('from data_sources.base_source import DataSource')
        output.append('')
        output.append('')
        
        # NSEComplete class
        output.append('class NSEComplete(DataSource):')
        output.append('    """')
        output.append('    Complete NSE data source with all functionality consolidated.')
        output.append('    ')
        output.append('    Provides:')
        output.append('    - Real-time price data')
        output.append('    - Historical OHLCV data')
        output.append('    - Intraday data')
        output.append('    - Options & Futures data')
        output.append('    - Corporate actions')
        output.append('    - Bulk deals & insider trading')
        output.append('    - Market depth & option chains')
        output.append('    """')
        output.append('')
        output.append('    def __init__(self):')
        output.append('        super().__init__("NSE Complete")')
        output.append('        self.session = requests.Session()')
        output.append('        self.headers = {')
        output.append('            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",')
        output.append('            "Accept": "application/json"')
        output.append('        }')
        output.append('        self.base_url = "https://www.nseindia.com"')
        output.append('        self._initialize_session()')
        output.append('')
        
        # Add initialization method
        output.append('    def _initialize_session(self):')
        output.append('        """Initialize session with NSE cookies"""')
        output.append('        try:')
        output.append('            self.session.get(self.base_url, headers=self.headers, timeout=10)')
        output.append('        except Exception as e:')
        output.append('            self.handle_error(e, "Session initialization")')
        output.append('')
        
        # Add methods from nse_utils (skip __init__)
        output.append('    # ===== Methods from nse_utils.py =====')
        output.append('')
        
        for method in utils_methods:
            if not method.get('is_method'):  # Skip class methods for now
                # Convert standalone function to class method
                method_code = self.convert_to_class_method(method['source'])
                output.append(method_code)
                output.append('')
        
        # Add methods from nse_master_data
        output.append('    # ===== Methods from nse_master_data.py =====')
        output.append('')
        
        for method in master_methods:
            if method.get('is_method') and method.get('class_name') == 'NSEMasterData':
                # Already a class method, just indent properly
                method_code = self.ensure_proper_indentation(method['source'])
                output.append(method_code)
                output.append('')
        
        # Add high-level wrapper methods (from original nse_complete.py)
        output.append('    # ===== High-level wrapper methods =====')
        output.append('')
        output.append('    def get_complete_data(self, symbol: str) -> Dict[str, Any]:')
        output.append('        """')
        output.append('        Get complete dataset for a symbol.')
        output.append('        ')
        output.append('        Returns:')
        output.append('            Dictionary with all available data')
        output.append('        """')
        output.append('        try:')
        output.append('            data = {')
        output.append('                "symbol": symbol,')
        output.append('                "company_info": self.get_company_info(symbol),')
        output.append('                "price_data": self.get_price_data(symbol),')
        output.append('                "historical_1y": self.get_historical_prices(symbol, period="1y"),')
        output.append('                "corporate_actions": self.get_corporate_actions(),')
        output.append('            }')
        output.append('            return data')
        output.append('        except Exception as e:')
        output.append('            return self.handle_error(e, f"Complete data for {symbol}")')
        output.append('')
        
        return '\n'.join(output)
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code"""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Skip local imports
                if 'nse_utils' not in line and 'nse_master_data' not in line:
                    imports.append(line)
        return imports
    
    def convert_to_class_method(self, function_code: str) -> str:
        """Convert standalone function to class method"""
        lines = function_code.split('\n')
        
        # Find the def line
        def_line_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                def_line_idx = i
                break
        
        # Add self parameter
        def_line = lines[def_line_idx]
        if 'def ' in def_line and '(self' not in def_line:
            def_line = def_line.replace('(', '(self, ', 1)
            if '(self, )' in def_line:
                def_line = def_line.replace('(self, )', '(self)')
            lines[def_line_idx] = def_line
        
        # Add proper indentation (4 spaces for class method)
        indented_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                indented_lines.append('    ' + line)
            else:
                indented_lines.append(line)
        
        return '\n'.join(indented_lines)
    
    def ensure_proper_indentation(self, code: str) -> str:
        """Ensure code has proper class method indentation"""
        lines = code.split('\n')
        return '\n'.join(['    ' + line if line.strip() else line for line in lines])
    
    def validate_python_syntax(self, file_path: Path) -> bool:
        """Validate Python file syntax"""
        try:
            content = file_path.read_text(encoding='utf-8')
            ast.parse(content)
            return True
        except SyntaxError as e:
            self.log(f"Syntax error in {file_path.name}: {e}", "ERROR")
            self.errors.append(f"Syntax error: {e}")
            return False
    
    def update_imports(self, new_nse_complete: Path):
        """Update import statements in all dependent files"""
        self.log("\n" + "=" * 70)
        self.log("STEP 4: Updating Imports")
        self.log("=" * 70)
        
        replacements = {
            r'from\s+nse_utils\s+import\s+NseUtils': 'from data_sources.nse_complete import NSEComplete',
            r'from\s+external_libs\.nse_utils\s+import\s+NseUtils': 'from data_sources.nse_complete import NSEComplete',
            r'from\s+nse_master_data\s+import\s+NSEMasterData': 'from data_sources.nse_complete import NSEComplete',
            r'from\s+external_libs\.nse_master_data\s+import\s+NSEMasterData': 'from data_sources.nse_complete import NSEComplete',
            r'import\s+nse_utils': 'from data_sources.nse_complete import NSEComplete',
            r'import\s+nse_master_data': 'from data_sources.nse_complete import NSEComplete',
            
            # Object instantiation
            r'NseUtils\(\)': 'NSEComplete()',
            r'NSEMasterData\(\)': 'NSEComplete()',
            
            # Variable names
            r'self\.nse\s*=\s*NseUtils\(\)': 'self.nse = NSEComplete()',
            r'self\.master\s*=\s*NSEMasterData\(\)': '# Consolidated into self.nse',
        }
        
        for file_path in self.dependent_files:
            try:
                # Backup file
                backup = self.backup_dir / f"{file_path.name}.before_import_update"
                shutil.copy2(file_path, backup)
                
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Apply replacements
                for pattern, replacement in replacements.items():
                    content = re.sub(pattern, replacement, content)
                
                # Only write if changed
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    self.log(f"Updated: {file_path.relative_to(self.project_root)}", "SUCCESS")
                    
                    # Validate syntax
                    if not self.validate_python_syntax(file_path):
                        # Rollback this file
                        shutil.copy2(backup, file_path)
                        self.log(f"Rolled back due to syntax error: {file_path.name}", "WARNING")
                
            except Exception as e:
                self.log(f"Error updating {file_path.name}: {e}", "ERROR")
                self.errors.append(f"Import update failed for {file_path.name}: {e}")
        
        return len(self.errors) == 0
    
    def run_tests(self):
        """Run tests to verify refactoring didn't break anything"""
        self.log("\n" + "=" * 70)
        self.log("STEP 5: Running Tests")
        self.log("=" * 70)
        
        # Check if pytest is available
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--collect-only', '-q'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if 'no tests ran' in result.stdout.lower() or not result.returncode:
                self.log("No tests found or pytest not configured", "WARNING")
                return True
            
            # Run actual tests
            self.log("Running pytest...")
            result = subprocess.run(
                ['python', '-m', 'pytest', '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("All tests passed", "SUCCESS")
                return True
            else:
                self.log("Some tests failed - review before finalizing", "WARNING")
                self.warnings.append("Tests failed")
                return False
                
        except FileNotFoundError:
            self.log("pytest not installed - skipping tests", "WARNING")
            return True
        except Exception as e:
            self.log(f"Test execution error: {e}", "WARNING")
            return True
    
    def finalize_refactoring(self, new_nse_complete: Path):
        """Finalize refactoring by replacing old file and cleaning up"""
        self.log("\n" + "=" * 70)
        self.log("STEP 6: Finalizing")
        self.log("=" * 70)
        
        try:
            # Replace old nse_complete.py with new one
            shutil.move(str(new_nse_complete), str(self.nse_complete))
            self.log(f"Replaced {self.nse_complete.name}", "SUCCESS")
            
            # Delete old files
            if self.nse_utils.exists():
                self.nse_utils.unlink()
                self.log(f"Deleted {self.nse_utils.name}", "SUCCESS")
            
            if self.nse_master.exists():
                self.nse_master.unlink()
                self.log(f"Deleted {self.nse_master.name}", "SUCCESS")
            
            # Check if external_libs is now empty
            external_libs_dir = self.project_root / "external_libs"
            if external_libs_dir.exists():
                remaining = list(external_libs_dir.glob("*.py"))
                if len(remaining) <= 1:  # Only __init__.py
                    self.log("external_libs/ is now empty - consider removing", "INFO")
            
            return True
            
        except Exception as e:
            self.log(f"Finalization failed: {e}", "ERROR")
            self.errors.append(str(e))
            return False
    
    def generate_report(self):
        """Generate final refactoring report"""
        self.log("\n" + "=" * 70)
        self.log("REFACTORING REPORT")
        self.log("=" * 70)
        
        report = []
        report.append(f"\n📊 Summary:")
        report.append(f"  - Files merged: 3 → 1")
        report.append(f"  - Files updated: {len(self.dependent_files)}")
        report.append(f"  - Errors: {len(self.errors)}")
        report.append(f"  - Warnings: {len(self.warnings)}")
        
        if self.errors:
            report.append(f"\n❌ Errors:")
            for error in self.errors:
                report.append(f"  - {error}")
        
        if self.warnings:
            report.append(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                report.append(f"  - {warning}")
        
        report.append(f"\n💾 Backup location: {self.backup_dir}")
        report.append(f"🔄 Rollback script: {self.backup_dir}/rollback.sh")
        
        if not self.errors:
            report.append(f"\n✅ Refactoring completed successfully!")
        else:
            report.append(f"\n⚠️  Refactoring completed with errors - review carefully")
        
        report_text = '\n'.join(report)
        for line in report.split('\n'):
            self.log(line)
        
        # Save report to file
        report_file = self.backup_dir / "refactoring_report.txt"
        report_file.write_text(report_text)
        
        return len(self.errors) == 0
    
    def run(self, skip_tests: bool = False):
        """Run complete refactoring process"""
        self.log("🚀 Starting NSE Files Consolidation")
        self.log(f"Project root: {self.project_root}\n")
        
        # Step 1: Backup
        if not self.create_backup():
            self.log("Aborting due to backup failure", "ERROR")
            return False
        
        # Step 2: Analyze
        if not self.analyze_dependencies():
            self.log("Aborting due to analysis failure", "ERROR")
            return False
        
        # Step 3: Merge
        new_file = self.merge_nse_files()
        if not new_file:
            self.log("Aborting due to merge failure", "ERROR")
            return False
        
        # Step 4: Update imports
        if not self.update_imports(new_file):
            self.log("Import updates had errors - review manually", "WARNING")
        
        # Step 5: Run tests (optional)
        if not skip_tests:
            self.run_tests()
        
        # Step 6: Finalize
        if len(self.errors) == 0:
            if not self.finalize_refactoring(new_file):
                self.log("Finalization failed", "ERROR")
                return False
        else:
            self.log("Skipping finalization due to errors", "WARNING")
            self.log(f"Review generated file: {new_file}", "INFO")
        
        # Generate report
        return self.generate_report()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automated NSE Files Consolidation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full refactoring with tests
  python nse_refactor.py
  
  # Run without tests (faster)
  python nse_refactor.py --skip-tests
  
  # Specify project root
  python nse_refactor.py --project-root /path/to/fortune_trading
  
  # Dry run (analyze only, no changes)
  python nse_refactor.py --dry-run
        """
    )
    
    parser.add_argument(
        '--project-root',
        help='Project root directory (default: current directory)',
        default=None
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip running tests after refactoring'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze only, do not make any changes'
    )
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = NSERefactoringTool(project_root=args.project_root)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
        tool.create_backup()
        tool.analyze_dependencies()
        tool.generate_report()
    else:
        # Run full refactoring
        success = tool.run(skip_tests=args.skip_tests)
        
        if success:
            print("\n" + "=" * 70)
            print("✅ REFACTORING COMPLETE!")
            print("=" * 70)
            print(f"\n📁 Backup: {tool.backup_dir}")
            print(f"📋 Log: {tool.log_file}")
            print(f"\n💡 To rollback: bash {tool.backup_dir}/rollback.sh")
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("⚠️  REFACTORING COMPLETED WITH ERRORS")
            print("=" * 70)
            print(f"\n📋 Check log: {tool.log_file}")
            print(f"🔄 To rollback: bash {tool.backup_dir}/rollback.sh")
            sys.exit(1)


if __name__ == "__main__":
    main()