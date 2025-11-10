#!/usr/bin/env python3
"""
Final Project Cleanup Script
Organizes Fortune Trading project structure
"""

import os
import shutil
from pathlib import Path
import argparse


class ProjectCleaner:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root or os.getcwd())
        self.deleted = []
        self.moved = []
        self.kept = []

    def log(self, message, emoji="ℹ️"):
        print(f"{emoji} {message}")

    def create_scripts_dir(self):
        """Create scripts directory if it doesn't exist"""
        scripts_dir = self.project_root / "scripts"
        existed = scripts_dir.exists()
        scripts_dir.mkdir(parents=True, exist_ok=True)
        if not existed:
            self.log("Created: scripts/", "📁")
        else:
            self.log("Found: scripts/", "📁")
        return scripts_dir

    def delete_temp_files(self, dry_run=False):
        """Delete temporary refactoring scripts"""
        self.log("\n" + "=" * 70)
        self.log("DELETING TEMPORARY FILES")
        self.log("=" * 70)

        temp_files = [
            "Refactoring.py",
            "fix_nse_merge.py",
            "quick_validate.py",
            "data_sources/nse_complete_ORIGINAL.py",
        ]

        for file_path in temp_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    if not dry_run:
                        full_path.unlink()
                        self.deleted.append(file_path)
                        self.log(f"Deleted: {file_path}", "❌")
                    else:
                        self.log(f"Would delete: {file_path}", "🔍")
                except IsADirectoryError:
                    # In case a directory was listed by mistake
                    if not dry_run:
                        shutil.rmtree(full_path, ignore_errors=True)
                        self.deleted.append(file_path + "/")
                        self.log(f"Deleted directory: {file_path}/", "❌")
                    else:
                        self.log(f"Would delete directory: {file_path}/", "🔍")
                except Exception as e:
                    self.log(f"Failed to delete {file_path}: {e}", "⚠️")
            else:
                self.log(f"Not found: {file_path}", "⚠️")

    def move_utility_scripts(self, dry_run=False):
        """Move utility scripts to scripts/ folder"""
        self.log("\n" + "=" * 70)
        self.log("MOVING UTILITY SCRIPTS")
        self.log("=" * 70)

        scripts_dir = self.create_scripts_dir()

        scripts_to_move = [
            "fix_corporate_actions.py",
            "structure.py",
            "validate_data.py",
            "stock_screener.py",
            "unified_exporter.py",
            "update_database.py",
        ]

        for script in scripts_to_move:
            source = self.project_root / script
            dest = scripts_dir / script

            if source.exists():
                if dest.exists():
                    self.log(f"Already in scripts/: {script} (skipping)", "⏭️")
                    continue
                if not dry_run:
                    try:
                        shutil.move(str(source), str(dest))
                        self.moved.append(f"{script} → scripts/")
                        self.log(f"Moved: {script} → scripts/", "🔄")
                    except Exception as e:
                        self.log(f"Failed to move {script}: {e}", "⚠️")
                else:
                    self.log(f"Would move: {script} → scripts/", "🔍")
            else:
                self.log(f"Not found: {script}", "⚠️")

    def cleanup_failed_backups(self, dry_run=False):
        """Remove failed refactoring backup folders"""
        self.log("\n" + "=" * 70)
        self.log("CLEANING UP FAILED BACKUPS")
        self.log("=" * 70)

        backups_to_delete = [
            "backups/refactor_20251028_001402",
            "backups/refactor_20251028_001446",
        ]

        for backup_path in backups_to_delete:
            full_path = self.project_root / backup_path
            if full_path.exists():
                if not dry_run:
                    try:
                        shutil.rmtree(full_path)
                        self.deleted.append(backup_path + "/")
                        self.log(f"Deleted: {backup_path}/", "❌")
                    except Exception as e:
                        self.log(f"Failed to delete {backup_path}/: {e}", "⚠️")
                else:
                    self.log(f"Would delete: {backup_path}/", "🔍")
            else:
                self.log(f"Not found: {backup_path}", "⚠️")

        # Keep the good backup
        good_backup_rel = "backups/refactor_20251028_001034"
        good_backup = self.project_root / good_backup_rel
        if good_backup.exists():
            self.kept.append(f"{good_backup_rel} (original files)")
            self.log(f"Keeping: {good_backup_rel}/ (original files)", "✅")

    def cleanup_pycache(self, dry_run=False):
        """Remove all __pycache__ directories"""
        self.log("\n" + "=" * 70)
        self.log("CLEANING PYTHON CACHE")
        self.log("=" * 70)

        found = 0
        removed = 0
        for pycache in self.project_root.rglob("__pycache__"):
            found += 1
            rel = pycache.relative_to(self.project_root)
            if not dry_run:
                try:
                    shutil.rmtree(pycache)
                    removed += 1
                except Exception as e:
                    self.log(f"Failed to remove: {rel} ({e})", "⚠️")
            else:
                self.log(f"Would delete: {rel}", "🔍")

        if dry_run:
            if found > 0:
                self.log(f"Found {found} __pycache__ directories (would remove)", "ℹ️")
            else:
                self.log("No __pycache__ directories found", "ℹ️")
        else:
            if removed > 0:
                self.log(f"Removed {removed} __pycache__ directories", "✅")
            else:
                self.log("No __pycache__ directories found", "ℹ️")

    def create_readme_for_scripts(self, dry_run=False):
        """Create README in scripts folder"""
        self.log("\n" + "=" * 70)
        self.log("CREATING DOCUMENTATION")
        self.log("=" * 70)

        scripts_dir = self.create_scripts_dir()
        readme = scripts_dir / "README.md"
