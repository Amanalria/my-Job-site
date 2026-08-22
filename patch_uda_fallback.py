import sys

with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

find_str = """        overview_html = self.humanize_overview(data)"""

replace_str = """        # GUARANTEE POST MATRIX (Fallback)
        if not data.get('post_matrix'):
            data['post_matrix'] = [{
                "name": data.get("organization", "Various Posts") + " Recruitment",
                "posts": data.get("total_posts", "See Notification"),
                "eligibility": "Please refer to the official notification linked below for detailed educational qualifications."
            }]
            
        # GUARANTEE HOW TO FILL (Fallback)
        if not data.get('how_to_fill'):
            if category in ['latest-jobs', 'admission']:
                data['how_to_fill'] = [
                    "Read the official recruitment notification carefully before applying.",
                    "Keep all basic documents ready: ID Proof, Address Details, Basic Details.",
                    "Ready your scanned documents like Photo, Signature, ID Proof, etc.",
                    "Click on the 'Apply Online' link given in the Important Links section below.",
                    "Fill out all the columns in the application form accurately.",
                    "Pay the required application fee if applicable.",
                    "Take a printout of the final submitted application form."
                ]
            else:
                data['how_to_fill'] = [
                    "Scroll down to the 'Important Links' section on this page.",
                    "Click on the direct link to download/check your status.",
                    "Enter your required login credentials such as Registration Number, Roll Number, or Date of Birth.",
                    "Click on submit to view your status.",
                    "Download and take a printout for future reference."
                ]

        overview_html = self.humanize_overview(data)"""

new_code = code.replace(find_str, replace_str)
with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Updated universal_design_agent.py with guaranteed fallbacks!")
