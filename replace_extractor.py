#!/usr/bin/env python3
"""
Script to replace the old extract_leadership_info function with the universal one.
"""

import re

def main():
    print("🔄 Replacing extraction function...")
    
    # Read universal extractor
    with open('universal_extractor.py', 'r', encoding='utf-8') as f:
        universal_content = f.read()
    
    # Extract the function (everything after def until end or next def)
    pattern = r'(def extract_leadership_info_universal\(.*?\n)(?=\n# Test|$)'
    match = re.search(pattern, universal_content, re.DOTALL)
    
    if not match:
        print("❌ Could not find universal function")
        return
    
    new_function = match.group(1).strip()
    
    # Rename the function
    new_function = new_function.replace('extract_leadership_info_universal', 'extract_leadership_info')
    
    # Read UI file
    with open('src/ui/url_chat_interface.py', 'r', encoding='utf-8') as f:
        ui_content = f.read()
    
    # Find the old function (from def to the next def)
    old_pattern = r'def extract_leadership_info\(.*?\n(?=def save_leaders_to_db)'
    
    # Replace it (use a function to avoid escape issues)
    def replacer(match):
        return new_function + '\n\n\n'
    
    new_ui_content = re.sub(old_pattern, replacer, ui_content, flags=re.DOTALL)
    
    if new_ui_content == ui_content:
        print("⚠️  No changes made - pattern might not have matched")
        return
    
    # Save the modified file
    with open('src/ui/url_chat_interface.py', 'w', encoding='utf-8') as f:
        f.write(new_ui_content)
    
    print("✅ Successfully replaced the function!")
    print(f"📊 Old file: {len(ui_content)} chars")
    print(f"📊 New file: {len(new_ui_content)} chars")
    print(f"📈 Difference: {len(new_ui_content) - len(ui_content):+} chars")

if __name__ == '__main__':
    main()
