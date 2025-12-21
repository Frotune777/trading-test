"""
Python Project Structure Analyzer - LLM Optimized
Generates compact, token-efficient project documentation
"""

import os
import ast
import sys
from pathlib import Path
import subprocess
from datetime import datetime

# Folders to exclude
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', 'env', '.venv', '.env', 'node_modules', 'dist', 'build'}

def find_git_root(start_path=None):
    """Find the root of the git repository."""
    try:
        if start_path is None:
            start_path = os.getcwd()
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=start_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def find_project_root():
    """Automatically detect project root directory."""
    git_root = find_git_root()
    if git_root:
        print(f"✅ Git repository: {git_root}")
        return git_root
    
    current = Path.cwd()
    markers = ['setup.py', 'pyproject.toml', 'requirements.txt', 'setup.cfg', 'Pipfile']
    
    for _ in range(3):
        for marker in markers:
            if (current / marker).exists():
                print(f"✅ Project root (found {marker}): {current}")
                return str(current)
        if current.parent == current:
            break
        current = current.parent
    
    script_dir = Path(__file__).parent.absolute()
    print(f"⚠️  Using script directory: {script_dir}")
    return str(script_dir)

def scan_python_files(base_dir):
    """Recursively find Python files."""
    py_files = []
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files

def compact_signature(func_node):
    """Generate ultra-compact function signature."""
    args = []
    for arg in func_node.args.args:
        name = arg.arg
        if arg.annotation:
            hint = ast.unparse(arg.annotation)
            args.append(f"{name}:{hint}")
        else:
            args.append(name)
    
    # Add defaults
    defaults = func_node.args.defaults
    if defaults:
        num_defaults = len(defaults)
        for i in range(len(args) - num_defaults, len(args)):
            default_val = ast.unparse(defaults[i - (len(args) - num_defaults)])
            args[i] = f"{args[i]}={default_val}"
    
    return f"{func_node.name}({', '.join(args)})"

def extract_compact_info(file_path, project_root):
    """Extract minimal essential information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        rel_path = os.path.relpath(file_path, project_root)
        
        # Extract imports (compact)
        imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Extract classes and functions
        items = []
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        sig = compact_signature(item)
                        doc = ast.get_docstring(item)
                        if doc:
                            doc = doc.split('\n')[0][:60]  # First line only, max 60 chars
                            methods.append(f"    {sig}  # {doc}")
                        else:
                            methods.append(f"    {sig}")
                
                class_doc = ast.get_docstring(node)
                class_info = f"class {node.name}"
                if node.bases:
                    bases = [ast.unparse(b) for b in node.bases]
                    class_info += f"({', '.join(bases)})"
                
                if class_doc:
                    class_info += f"  # {class_doc.split(chr(10))[0][:60]}"
                
                items.append(class_info)
                items.extend(methods)
            
            elif isinstance(node, ast.FunctionDef):
                sig = compact_signature(node)
                doc = ast.get_docstring(node)
                if doc:
                    doc = doc.split('\n')[0][:60]
                    items.append(f"def {sig}  # {doc}")
                else:
                    items.append(f"def {sig}")
        
        return {
            'path': rel_path,
            'imports': sorted(imports),
            'items': items,
            'lines': len(content.splitlines())
        }
    
    except Exception as e:
        return {
            'path': os.path.relpath(file_path, project_root),
            'error': str(e)
        }

def generate_tree_structure(files, project_root):
    """Generate compact tree structure."""
    tree_lines = []
    
    # Group by directory
    dirs = {}
    for file_info in files:
        if 'error' in file_info:
            continue
        
        path_parts = file_info['path'].split(os.sep)
        if len(path_parts) == 1:
            dir_name = '.'
        else:
            dir_name = os.sep.join(path_parts[:-1])
        
        if dir_name not in dirs:
            dirs[dir_name] = []
        dirs[dir_name].append(file_info)
    
    for dir_name in sorted(dirs.keys()):
        if dir_name != '.':
            tree_lines.append(f"\n{dir_name}/")
        for file_info in sorted(dirs[dir_name], key=lambda x: x['path']):
            filename = os.path.basename(file_info['path'])
            tree_lines.append(f"  {filename} ({file_info['lines']} lines)")
    
    return '\n'.join(tree_lines)

def generate_compact_output(project_root, files):
    """Generate ultra-compact text output optimized for LLM."""
    output_lines = []
    
    # Header
    output_lines.append("=" * 70)
    output_lines.append(f"PROJECT: {os.path.basename(project_root)}")
    output_lines.append(f"PATH: {project_root}")
    output_lines.append(f"ANALYZED: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output_lines.append("=" * 70)
    
    # Summary
    total_files = len([f for f in files if 'error' not in f])
    total_lines = sum(f.get('lines', 0) for f in files if 'error' not in f)
    all_imports = set()
    for f in files:
        if 'imports' in f:
            all_imports.update(f['imports'])
    
    output_lines.append(f"\n📊 SUMMARY: {total_files} files, {total_lines:,} lines")
    output_lines.append(f"📦 DEPENDENCIES: {', '.join(sorted(all_imports))}")
    
    # Tree structure
    output_lines.append("\n📁 FILE TREE:")
    output_lines.append(generate_tree_structure(files, project_root))
    
    # Detailed structure
    output_lines.append("\n" + "=" * 70)
    output_lines.append("📋 DETAILED STRUCTURE")
    output_lines.append("=" * 70)
    
    for file_info in sorted(files, key=lambda x: x['path']):
        if 'error' in file_info:
            output_lines.append(f"\n❌ {file_info['path']}: {file_info['error']}")
            continue
        
        output_lines.append(f"\n📄 {file_info['path']}")
        
        if file_info.get('imports'):
            output_lines.append(f"   imports: {', '.join(file_info['imports'])}")
        
        if file_info.get('items'):
            for item in file_info['items']:
                output_lines.append(f"   {item}")
    
    return '\n'.join(output_lines)

def generate_markdown_output(project_root, files):
    """Generate compact markdown output."""
    lines = []
    
    # Title
    lines.append(f"# {os.path.basename(project_root)}\n")
    lines.append(f"**Path:** `{project_root}`  ")
    lines.append(f"**Analyzed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Summary
    total_files = len([f for f in files if 'error' not in f])
    total_lines = sum(f.get('lines', 0) for f in files if 'error' not in f)
    
    lines.append("## Summary\n")
    lines.append(f"- **Files:** {total_files}")
    lines.append(f"- **Lines:** {total_lines:,}")
    
    all_imports = set()
    for f in files:
        if 'imports' in f:
            all_imports.update(f['imports'])
    
    lines.append(f"- **Dependencies:** {', '.join(sorted(all_imports))}\n")
    
    # Structure by file
    lines.append("## Structure\n")
    
    current_dir = None
    for file_info in sorted(files, key=lambda x: x['path']):
        if 'error' in file_info:
            continue
        
        # Group by directory
        dir_name = os.path.dirname(file_info['path']) or '.'
        if dir_name != current_dir:
            current_dir = dir_name
            lines.append(f"\n### `{dir_name}/`\n")
        
        filename = os.path.basename(file_info['path'])
        lines.append(f"#### {filename} ({file_info['lines']} lines)\n")
        
        if file_info.get('imports'):
            lines.append(f"**Imports:** `{', '.join(file_info['imports'])}`\n")
        
        if file_info.get('items'):
            lines.append("```python")
            for item in file_info['items']:
                lines.append(item)
            lines.append("```\n")
    
    return '\n'.join(lines)

def generate_minimal_json(project_root, files):
    """Generate minimal JSON (more compact than original)."""
    import json
    
    data = {
        "project": os.path.basename(project_root),
        "files": {}
    }
    
    for f in files:
        if 'error' not in f:
            data["files"][f['path']] = {
                "i": f.get('imports', []),  # imports
                "s": f.get('items', []),     # structure
                "l": f.get('lines', 0)       # lines
            }
    
    return json.dumps(data, separators=(',', ':'))

def save_outputs(project_root, files):
    """Save multiple output formats."""
    outputs = {}
    
    # 1. Compact Text (smallest, most readable)
    txt_file = os.path.join(project_root, "PROJECT_STRUCTURE.txt")
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(generate_compact_output(project_root, files))
    outputs['text'] = txt_file
    print(f"💾 Text:     {txt_file} ({os.path.getsize(txt_file):,} bytes)")
    
    # 2. Markdown (good for LLM, GitHub)
    md_file = os.path.join(project_root, "PROJECT_STRUCTURE.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(generate_markdown_output(project_root, files))
    outputs['markdown'] = md_file
    print(f"💾 Markdown: {md_file} ({os.path.getsize(md_file):,} bytes)")
    
    # 3. Minimal JSON (if still needed)
    json_file = os.path.join(project_root, "project_structure.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(generate_minimal_json(project_root, files))
    outputs['json'] = json_file
    print(f"💾 JSON:     {json_file} ({os.path.getsize(json_file):,} bytes)")
    
    return outputs

def main():
    """Main function."""
    print("🚀 Python Project Analyzer (LLM Optimized)")
    print("=" * 70)
    
    # Get project root
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = find_project_root()
    
    if not os.path.exists(project_root):
        print(f"❌ Error: Path does not exist: {project_root}")
        sys.exit(1)
    
    # Scan files
    print(f"\n🔍 Scanning: {project_root}")
    py_files = scan_python_files(project_root)
    print(f"📁 Found {len(py_files)} Python files")
    
    # Extract info
    print("\n📊 Extracting structure...")
    files_info = []
    for i, file_path in enumerate(py_files, 1):
        print(f"  [{i}/{len(py_files)}] {os.path.basename(file_path)}", end='\r')
        files_info.append(extract_compact_info(file_path, project_root))
    
    print("\n")
    
    # Save outputs
    print("💾 Saving outputs...")
    outputs = save_outputs(project_root, files_info)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"📂 Project: {os.path.basename(project_root)}")
    print(f"📄 Files:   {len(files_info)}")
    print(f"📝 Lines:   {sum(f.get('lines', 0) for f in files_info):,}")
    print("\n🎯 Recommended for LLM: PROJECT_STRUCTURE.txt or .md")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)