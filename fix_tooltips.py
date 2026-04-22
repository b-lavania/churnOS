import os
import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # The error pattern is:
    # float(template.get("aov", 65.0, help="..."))
    # float(config["monthly_churn_rate"] * 100, help="..."),
    
    # Let's just remove any `, help="..."` that is immediately followed by a `)`
    # This might accidentally remove it from `st.slider(..., help="...")` if there's no comma after the help.
    # But wait, st.slider(..., help="...") is usually at the end, so it has a `)` after it.
    
    # We only want to remove it from `template.get(...)` and `config[...]` context.
    # Pattern 1: `template.get(..., help="...")`
    # Pattern 2: `config[...], help="..."`
    
    # Better approach:
    # Look for: `template.get([^)]*?), help="([^"]*)"\)`
    # Replace with: `template.get(\1)`
    content = re.sub(r'(template\.get\([^)]*?),\s*help="[^"]*"\)', r'\1)', content)
    
    # Look for: `config\[[^\]]*?\](?:[\s\*\d\.]*),\s*help="[^"]*"\)`
    content = re.sub(r'(config\[[^\]]*?\][^,]*?),\s*help="[^"]*"\)', r'\1)', content)

    with open(filepath, 'w') as f:
        f.write(content)

for root, dirs, files in os.walk('pages'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_file(filepath)

print("Fix applied.")
