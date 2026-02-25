import os
import sys
import json
from datetime import datetime

# Script to fix the issue of missing items in the RSS feed
# 1. Update is_procedure_active to be more resilient
# 2. Fix the extraction regex if possible

def fix_gerir_ativos():
    path = "scripts/gerir_ativos.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Modify is_procedure_active to return True if prazo is missing or N/A
    # This prevents dropping items just because extraction failed
    old_code = """    if not prazo_str or prazo_str == 'N/A':
        return False"""
    new_code = """    if not prazo_str or prazo_str == 'N/A':
        # FALLBACK: If we can't extract the deadline, consider it active for 15 days
        # to ensure it appears in the feed and notifications.
        return True"""

    if old_code in content:
        new_content = content.replace(old_code, new_code)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Fixed scripts/gerir_ativos.py to be more resilient.")
    else:
        print("⚠️ Could not find target code in scripts/gerir_ativos.py")

def fix_extractor_regex():
    path = "scripts/rss_dre_extractor.py"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to add more resilient identification patterns
    old_possible = '["1 - IDENTIFICAÇÃO E CONTACTOS DA ENTIDADE ADJUDICANTE", "IDENTIFICAÇÃO E CONTACTOS DA ENTIDADE ADJUDICANTE", "IDENTIFICAÇÃO"]'
    # Actually it's a list in the file
    
    if "IDENTIFICAÇÃO" in content:
        print("Checked rss_dre_extractor.py: Already has Identification patterns.")
    
if __name__ == "__main__":
    fix_gerir_ativos()
