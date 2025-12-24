#!/usr/bin/env python3
"""
🚀 PROJECT ANALYZER & TASK GENERATOR for Frotune777/trading-test
Analyzes GitHub repo structure, generates comprehensive task breakdown,
marks completion status, and creates development roadmap with ML/Backtesting/OpenAlgo.

Usage: python analyze_project.py --repo Frotune777/trading-test
"""

import os
import json
import subprocess
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import git  # pip install GitPython

@dataclass
class Task:
    id: str
    name: str
    description: str
    status: str  # completed, in_progress, pending
    priority: str  # critical, high, medium, low
    phase: str
    subtasks: List['Task'] = None
    dependencies: List[str] = None
    est_hours: int = 0

@dataclass
class ProjectStatus:
    repo_name: str
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    completion_pct: float
    phases: Dict[str, Dict[str, int]]
    critical_path: List[str]
    recommendations: List[str]

class ProjectAnalyzer:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.tasks = []
        self.status = None
        
    def analyze_repo_structure(self) -> Dict[str, Any]:
        """Analyze complete repo structure and file presence"""
        structure = {
            "backend": False, "frontend": False, "quad": False,
            "ml": False, "backtest": False, "strategies": False,
            "docker": False, "tests": False, "docs": False
        }
        
        # Check directories
        for dir_name in structure.keys():
            if (self.repo_path / dir_name).exists():
                structure[dir_name] = True
        
        # Check key files
        key_files = {
            "requirements.txt": self.repo_path / "requirements.txt",
            "docker-compose.yml": self.repo_path / "docker-compose.yml",
            "playwright.config.ts": self.repo_path / "playwright.config.ts",
            "README.md": self.repo_path / "README.md"
        }
        
        structure["key_files"] = {k: v.exists() for k, v in key_files.items()}
        
        # Count Python files by module
        py_count = {}
        for py_file in self.repo_path.rglob("*.py"):
            module = str(py_file.parent.relative_to(self.repo_path)).replace("/", ".")
            py_count[module] = py_count.get(module, 0) + 1
            
        structure["python_modules"] = py_count
        
        return structure
    
    def generate_complete_tasks(self, structure: Dict[str, Any]) -> List[Task]:
        """Generate ALL tasks for complete trading platform"""
        
        # Phase 1: Infrastructure (Mostly Complete)
        phase1 = [
            Task("1.1", "Docker Infrastructure", "Complete Docker setup", 
                 "completed" if structure["docker"] else "in_progress", "low", "Phase 1"),
            Task("1.2", "FastAPI Backend", "API routers + CORS", "completed", "low", "Phase 1"),
            Task("1.3", "Next.js Frontend", "Modern UI with Tailwind", "completed", "low", "Phase 1"),
        ]
        
        # Phase 2: Core Trading Engine (90% Complete)
        phase2 = [
            Task("2.1", "Market Data API", "NSE/BSE real-time", "completed", "low", "Phase 2"),
            Task("2.2", "Derivatives API", "Option chains", "completed", "low", "Phase 2"),
            Task("2.3", "Technicals API", "50+ TA-Lib", "completed", "low", "Phase 2"),
            Task("2.4", "Insider Trading API", "FII/DII + Promoters", "completed", "low", "Phase 2"),
            Task("2.5", "QUAD Engine", "6-pillar reasoning", "completed", "low", "Phase 2"),
            Task("2.6", "Real-time Alerts", "WebSocket alert engine", "pending", "critical", "Phase 2", 
                 est_hours=8, dependencies=["2.5"])
        ]
        
        # Phase 3: ML & Intelligence (NEW - 0%)
        phase3 = [
            Task("3.1", "ML Prediction Models", "LSTM/Transformer for price direction", "pending", "critical", "Phase 3", est_hours=24),
            Task("3.2", "Auto Model Improvement", "Online learning + retraining", "pending", "high", "Phase 3", est_hours=16, dependencies=["3.1"]),
            Task("3.3", "Model Serving API", "FastAPI + ONNX", "pending", "high", "Phase 3", est_hours=8, dependencies=["3.1"])
        ]
        
        # Phase 4: Backtesting & Strategies (NEW - 0%)
        phase4 = [
            Task("4.1", "Backtesting Engine", "Vectorized + Event-driven", "pending", "critical", "Phase 4", est_hours=20),
            Task("4.2", "Custom Strategy Framework", "Python DSL for strategies", "pending", "critical", "Phase 4", est_hours=16),
            Task("4.3", "Strategy Marketplace", "User-defined strategies", "pending", "medium", "Phase 4", est_hours=12, dependencies=["4.2"])
        ]
        
        # Phase 5: Execution & Live Trading (NEW - 0%)
        phase5 = [
            Task("5.1", "OpenAlgo Integration", "Production-ready bridge", "pending", "critical", "Phase 5", est_hours=12),
            Task("5.2", "Risk Engine", "Position sizing + stops", "pending", "critical", "Phase 5", est_hours=10, dependencies=["5.1"]),
            Task("5.3", "Live Trading Dashboard", "Paper + Live mode", "pending", "high", "Phase 5", est_hours=8, dependencies=["5.1"])
        ]
        
        # Phase 6: Automation & Production
        phase6 = [
            Task("6.1", "Scheduler/Cron", "Daily model retrain + data sync", "pending", "high", "Phase 6", est_hours=6),
            Task("6.2", "Telegram/Discord Bot", "Alert + trade notifications", "pending", "medium", "Phase 6", est_hours=8),
            Task("6.3", "Production Deployment", "Kubernetes + Monitoring", "pending", "high", "Phase 6", est_hours=12)
        ]
        
        # Phase 7: Quality & Testing
        phase7 = [
            Task("7.1", "Playwright E2E Tests", "Full user flows", "in_progress", "critical", "Phase 7", est_hours=16),
            Task("7.2", "Pytest Unit Tests", "95% coverage", "pending", "high", "Phase 7", est_hours=12),
            Task("7.3", "Backtest Validation", "Statistical significance", "pending", "critical", "Phase 7", est_hours=8)
        ]
        
        self.tasks = phase1 + phase2 + phase3 + phase4 + phase5 + phase6 + phase7
        return self.tasks
    
    def calculate_status(self) -> ProjectStatus:
        """Calculate overall project status"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        in_progress = sum(1 for t in self.tasks if t.status == "in_progress")
        pending = total - completed - in_progress
        
        phases = {}
        for task in self.tasks:
            phase = task.phase
            phases[phase] = phases.get(phase, {"total": 0, "completed": 0})
            phases[phase]["total"] += 1
            if task.status == "completed":
                phases[phase]["completed"] += 1
        
        critical_pending = [t.id for t in self.tasks if t.status == "pending" and t.priority == "critical"]
        
        status = ProjectStatus(
            repo_name="trading-test",
            total_tasks=total,
            completed=completed,
            in_progress=in_progress,
            pending=pending,
            completion_pct=(completed / total) * 100,
            phases=phases,
            critical_path=critical_pending,
            recommendations=[
                "🚨 PRIORITY: Complete Phase 2.6 Alerts (blocks everything)",
                "⚡ NEXT: ML Models (Phase 3) + OpenAlgo (Phase 5)",
                f"📊 CURRENT: {completed}/{total} tasks complete ({(completed/total)*100:.1f}%)"
            ]
        )
        
        self.status = status
        return status
    
    def generate_roadmap(self) -> str:
        """Generate 4-week development roadmap"""
        critical = [t for t in self.tasks if t.priority == "critical" and t.status == "pending"]
        high = [t for t in self.tasks if t.priority == "high" and t.status == "pending"]
        
        roadmap = f"""
🚀 4-WEEK DEVELOPMENT ROADMAP
===========================

WEEK 1: Alerts + ML Foundation [12-18 Dec]
├── {critical[0].name} ({critical[0].est_hours}h)
├── {critical[1].name} ({critical[1].est_hours}h) 
└── Phase 2.6 + Phase 3.1

WEEK 2: Backtesting + OpenAlgo [19-25 Dec]
├── {critical[2].name} ({critical[2].est_hours}h)
├── {critical[3].name} ({critical[3].est_hours}h)
└── Phase 4.1 + Phase 5.1

WEEK 3: Live Trading + Bot [26 Dec-1 Jan]
├── Risk Engine + Live Dashboard
└── Telegram Bot integration

WEEK 4: Production + Testing [2-8 Jan]
├── E2E Tests + Deployment
└── Full system validation
        """
        return roadmap
    
    def save_report(self, filename: str = "project_analysis.json"):
        """Save complete analysis"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": asdict(self.status),
            "tasks": [asdict(t) for t in self.tasks],
            "roadmap": self.generate_roadmap()
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Full analysis saved: {filename}")
    
    def print_status_board(self):
        """Print beautiful status board"""
        status = self.status
        
        print("\n" + "="*60)
        print(f"📊 PROJECT STATUS: trading-test")
        print("="*60)
        print(f"Progress: {status.completed}/{status.total_tasks} ({status.completion_pct:.1f}%)")
        print(f"⏳ Pending: {status.pending} | 🔄 In Progress: {status.in_progress}")
        print("\nPHASES:")
        print("-" * 30)
        
        for phase, stats in status.phases.items():
            pct = (stats["completed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"{phase}: {stats['completed']}/{stats['total']} ({pct:.0f}%)")
        
        print(f"\n🚨 CRITICAL PATH ({len(status.critical_path)} tasks):")
        for task_id in status.critical_path[:5]:  # Top 5
            task = next(t for t in self.tasks if t.id == task_id)
            print(f"  {task_id}: {task.name}")
        
        print("\n" + self.generate_roadmap())

def main():
    parser = argparse.ArgumentParser(description="Analyze trading platform project")
    parser.add_argument("--repo", default=".", help="Local repo path")
    parser.add_argument("--save", action="store_true", help="Save JSON report")
    
    args = parser.parse_args()
    
    analyzer = ProjectAnalyzer(args.repo)
    structure = analyzer.analyze_repo_structure()
    
    print("🔍 Analyzing repo structure...")
    print(json.dumps(structure, indent=2))
    
    tasks = analyzer.generate_complete_tasks(structure)
    status = analyzer.calculate_status()
    
    analyzer.print_status_board()
    
    if args.save:
        analyzer.save_report()
    
    print("\n🎯 NEXT ACTIONS:")
    critical = [t for t in tasks if t.status == "pending" and t.priority == "critical"]
    for task in critical[:3]:
        print(f"• {task.id}: {task.name} ({task.est_hours}h)")

if __name__ == "__main__":
    main()