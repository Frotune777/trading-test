import sys
import os
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import configparser

# Define paths relative to this service
APP_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = APP_DIR.parent
PKSCREENER_PATH = BACKEND_DIR / "pkscreener"

class PKScreenerService:
    """
    Service adapter for the PKScreener library.
    Handles async subprocess execution, configuration management, and result parsing.
    """
    
    def __init__(self):
        self.env = os.environ.copy()
        # Ensure pkscreener imports work
        self.env["PYTHONPATH"] = f"{PKSCREENER_PATH}:{self.env.get('PYTHONPATH', '')}"
        self.env["RUNNER"] = "1"  # Bypass OTP/Telegram bot interaction
        
        # Default parameter injections for interactive strategies (from trader_start)
        self.STRATEGY_DEFAULTS = {
            "6": ":1",   # Reversal -> Buy Signals
            "7": ":1",   # Chart Patterns -> Bullish Inside Bar
            "9": ":2.5", # Volume Shockers -> Ratio 2.5
            "10": ":2",  # Kellner Channels
            "21": ":1",  # MF/FIIs -> Bought by MFs
        }

    async def run_scan(self, 
                       scan_option: str = "X", 
                       index_option: str = "12", 
                       scan_sub_option: str = "9",
                       stock_list: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Runs a PKScreener scan using subprocess.
        """
        extra_params = self.STRATEGY_DEFAULTS.get(str(scan_sub_option), "")
        options_str = f"{scan_option}:{index_option}:{scan_sub_option}{extra_params}"
        
        # Build command
        cli_path = PKSCREENER_PATH / "pkscreener" / "pkscreenercli.py"
        cmd = [
            "python3", 
            str(cli_path),
            "-a", "Y", # Auto-answer Yes
            "-o", options_str,
            "-e" # Exit after finishing
        ]
        
        if stock_list:
            cmd.extend(["--stocklist", ",".join(stock_list)])
            
        print(f"Executing PKScreener: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=self.env,
                cwd=str(BACKEND_DIR)
            )
            
            # Acceptance of defaults
            stdout, stderr = await process.communicate(input=b'\n\n\n\n\n')
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                print(f"PKScreener Error: {error_msg}")
                # We still try to find result file as some "errors" are just warnings
                
            return self._find_latest_result()

        except Exception as e:
            print(f"Failed to run PKScreener scan: {e}")
            return pd.DataFrame()

    def _find_latest_result(self) -> pd.DataFrame:
        """
        Locate and parse the most recent scan report (CSV/XLSX).
        """
        results_dir = BACKEND_DIR / "results"
        if not results_dir.exists():
            return pd.DataFrame()
            
        # PKScreener typically names reports with date/time stamps
        files = list(results_dir.rglob("*.csv")) + list(results_dir.rglob("*.xlsx"))
        if not files:
            return pd.DataFrame()
            
        latest_file = max(files, key=os.path.getctime)
        
        try:
            if latest_file.suffix == '.csv':
                return pd.read_csv(latest_file)
            else:
                return pd.read_excel(latest_file)
        except Exception as e:
            print(f"Error parsing {latest_file}: {e}")
            return pd.DataFrame()

    def update_config(self, settings: Dict[str, Any]) -> bool:
        """
        Dynamically updates pkscreener.ini.
        """
        config_path = BACKEND_DIR / "pkscreener.ini"
        if not config_path.exists():
            return False
            
        try:
            parser = configparser.ConfigParser(strict=False)
            parser.read(config_path)
            
            for key, value in settings.items():
                section, option = key.split('.', 1) if '.' in key else ('config', key)
                if not parser.has_section(section):
                    parser.add_section(section)
                parser.set(section, option, str(value))
                
            with open(config_path, 'w') as f:
                parser.write(f)
            return True
        except Exception as e:
            print(f"Config update failed: {e}")
            return False

# Initialize singleton
pkscreener_service = PKScreenerService()
