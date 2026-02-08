
import os
import sys

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, os.path.join(project_root, "src"))

from jojo_trading.utils.ai_client import AIClient

def get_directory_structure(root_dir, max_depth=2):
    structure = []
    root_dir = os.path.abspath(root_dir)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        depth = dirpath[len(root_dir):].count(os.sep)
        if depth > max_depth:
            continue
        indent = "  " * depth
        structure.append(f"{indent}{os.path.basename(dirpath)}/")
        for f in filenames:
            structure.append(f"{indent}  {f}")
    return "\n".join(structure)

def main():
    # Get structure
    root_path = os.path.join(os.path.dirname(__file__), "..", "..") # scripts/analyze/ -> root
    structure = get_directory_structure(root_path)
    
    # Read walkthrough if exists
    walkthrough_path = os.path.join(root_path, "walkthrough.md")
    walkthrough_content = ""
    if os.path.exists(walkthrough_path):
        with open(walkthrough_path, "r", encoding="utf-8") as f:
            walkthrough_content = f.read()
            
    prompt = f"""
    You are a Senior Software Architect.
    I have reorganized the 'jojo_trading' project.
    
    Project Structure:
    ```
    {structure}
    ```
    
    Walkthrough:
    ```
    {walkthrough_content}
    ```
    
    Review this organization. Is the separation of 'desktop_app' and 'web_app' reasonable?
    """
    
    print("Consulting Gemini (via Robust AIClient)...")
    client = AIClient()
    response = client.generate_content(prompt)
    
    print("\n=== Gemini Review ===\n")
    print(response)
    print("\n=====================")

if __name__ == "__main__":
    main()
