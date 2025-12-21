import ast
import os
from pathlib import Path

# -------------------------
# CONFIGURATION
# -------------------------
PROJECT_ROOT = Path(__file__).parent  # adjust if running from another location
EXCLUDE_DIRS = {"__pycache__", ".git", "venv", "env", "node_modules"}

# Domains mapping (folder keywords -> domain name)
DOMAIN_KEYWORDS = {
    "api": "API FILES",
    "config": "CONFIG FILES",
    "database": "DATA FILES",
    "core": "LOGIC FILES",
    "ml": "MODEL FILES",
    "services": "SERVICE FILES",
    "frontend": "FRONTEND FILES",
    "legacy": "LEGACY FILES",
}

# -------------------------
# FUNCTION DEFINITIONS
# -------------------------
def find_python_files(root: Path):
    """Recursively find all Python files, excluding system folders."""
    files = []
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files

def extract_defs(file_path: Path):
    """Extract top-level class and function names from a Python file."""
    defs = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                defs.append(f"class {node.name}")
            elif isinstance(node, ast.FunctionDef):
                defs.append(f"def {node.name}()")
    except Exception as e:
        defs.append(f"# Error parsing file: {e}")
    return defs

def infer_domain(file_path: Path):
    """Infer the domain based on path keywords."""
    lower_path = str(file_path).lower()
    for keyword, domain in DOMAIN_KEYWORDS.items():
        if f"/{keyword}/" in lower_path or lower_path.startswith(keyword):
            return domain
    return "MISC FILES"

# -------------------------
# MAIN SCAN AND SUMMARY
# -------------------------
def main():
    python_files = find_python_files(PROJECT_ROOT)
    summary = {}

    for file_path in python_files:
        domain = infer_domain(file_path)
        defs = extract_defs(file_path)
        if domain not in summary:
            summary[domain] = []
        summary[domain].append({"path": str(file_path.relative_to(PROJECT_ROOT)), "defs": defs})

    # -------------------------
    # OUTPUT TO FILE
    # -------------------------
    output_file = PROJECT_ROOT / "project_summary.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write(f"PROJECT: {PROJECT_ROOT.name}\n")
        f.write(f"ANALYZED: {Path().resolve()}\n")
        f.write("="*60 + "\n\n")

        for domain, files in summary.items():
            f.write(f"## {domain}\n\n")
            for file in files:
                defs_str = ", ".join(file["defs"]) if file["defs"] else "No defs"
                f.write(f"• {file['path']} - {defs_str}\n")
            f.write("\n")

        f.write("="*60 + "\n")
        f.write("Notes:\n")
        f.write("- Only main class/function names included\n")
        f.write("- System folders excluded (__pycache__, .git, venv, etc.)\n")
        f.write("- Ready for LLM-friendly analysis\n")
        f.write("="*60 + "\n")

    print(f"✅ Project summary saved to {output_file}")

# -------------------------
# RUN SCRIPT
# -------------------------
if __name__ == "__main__":
    main()
