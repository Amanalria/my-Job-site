with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

find_overview = '''    def humanize_overview(self, data: Dict[str, Any]) -> str:
        org = data.get("organization", "Government Authority")
        title = data.get("title", "Recruitment 2026")'''

replace_overview = '''    def humanize_overview(self, data: Dict[str, Any]) -> str:
        title = data.get("title", "Recruitment 2026")
        org = data.get("organization")
        if not org or org in ["Govt Board", "Recruitment Authority", "Government Authority"] or len(org) <= 5 or org in ["Uttar", "Bihar", "State", "Madhya", "Rajasthan"]:
            org = extract_clean_organization(title, default="Government Authority")'''

code = code.replace(find_overview, replace_overview)

with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated humanize_overview to use extract_clean_organization!")
