import sys

with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

find_block = """<table style="border-collapse: collapse; width: 100%; height: 150px;">
<tbody>
<tr style="height: 25px;">
<td colspan="2" style="width: 50%; text-align: center; height: 25px;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong> {tbl1_title} </strong></span></td>
</tr>
<tr style="height: 25px;">
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Category / Particulars</strong></span></td>
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Count / Status</strong></span></td>
</tr>
{cat_rows}
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th1}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th2}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th3}</th>
</tr>
{post_rows}
</tbody>
</table>"""

replace_block = """{cat_table_html}
{post_table_html}"""

new_code = code.replace(find_block, replace_block)

# Now we need to define `cat_table_html` and `post_table_html` higher up where `cat_rows` and `post_rows` are defined.
# In `build_post_html`:
python_find = """        cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in data.get("category_vacancies", {}).items()])

        post_rows = ""
        for p_item in data.get("post_matrix", []):"""

python_replace = """        cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in data.get("category_vacancies", {}).items()])
        cat_table_html = ""
        if cat_rows:
            cat_table_html = f'''<table style="border-collapse: collapse; width: 100%; height: 150px;">
<tbody>
<tr style="height: 25px;">
<td colspan="2" style="width: 50%; text-align: center; height: 25px;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong> {tbl1_title} </strong></span></td>
</tr>
<tr style="height: 25px;">
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Category / Particulars</strong></span></td>
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Count / Status</strong></span></td>
</tr>
{cat_rows}
</tbody>
</table>
<p>&nbsp;</p>'''

        post_rows = ""
        for p_item in data.get("post_matrix", []):"""

new_code = new_code.replace(python_find, python_replace)

python_find_2 = """        how_to_steps = "".join([f'<li style="margin-bottom:6px; text-align: left !important;">{s}</li>' for s in data.get("how_to_fill", [])])"""

python_replace_2 = """        post_table_html = ""
        if post_rows:
            post_table_html = f'''<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th1}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th2}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th3}</th>
</tr>
{post_rows}
</tbody>
</table>
<p>&nbsp;</p>'''

        how_to_steps = "".join([f'<li style="margin-bottom:6px; text-align: left !important;">{s}</li>' for s in data.get("how_to_fill", [])])"""

new_code = new_code.replace(python_find_2, python_replace_2)

with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Updated universal_design_agent.py to make tables conditional!")
