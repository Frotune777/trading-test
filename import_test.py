import os
import ast
import sys
import importlib.util

# -------------------------
# CONFIGURATION
# -------------------------
PROJECT_DIR = "."  # Root folder of your project
OUTPUT_FILE = "requirements_generated.txt"
EXCLUDE_DIRS = {"venv", ".venv", "__pycache__", "migration_venv"}  # folders to skip

# -------------------------
# Helper functions
# -------------------------
def is_std_lib(module_name: str) -> bool:
    """Check if a module is part of the standard library."""
    if module_name in sys.builtin_module_names:
        return True
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            return False
        return "site-packages" not in spec.origin and "dist-packages" not in spec.origin
    except ModuleNotFoundError:
        return False

def extract_imports(file_path: str) -> set:
    """Extract imported modules from a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=file_path)
    imports = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for name in n.names:
                imports.add(name.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.add(n.module.split(".")[0])
    return imports

def scan_folder(folder: str) -> set:
    """Scan folder recursively for Python files and collect imports."""
    all_imports = set()
    for root, dirs, files in os.walk(folder):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith(".py"):
                try:
                    imports = extract_imports(os.path.join(root, file))
                    all_imports.update(imports)
                except Exception as e:
                    print(f"⚠️ Skipping {file}: {e}")
    return all_imports

# -------------------------
# MAIN SCRIPT
# -------------------------
if __name__ == "__main__":
    print("🔎 Scanning project for imports...")
    imports = scan_folder(PROJECT_DIR)

    print(f"Total imports found: {len(imports)}")
    # Filter stdlib & private/internal modules
    third_party = sorted([i for i in imports if not is_std_lib(i) and not i.startswith("_")])

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pkg in third_party:
            f.write(pkg + "\n")

    print(f"✅ Done! {len(third_party)} third-party packages written to '{OUTPUT_FILE}'")
