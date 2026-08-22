import sys
with open('/root/sarkari-result-portal/fact_checker_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

find_str = """                            # 1. Post Matrix
                            if 'vacancy details' in text and 'total' in text and 'category wise' not in text:
                                i += 1
                                if i < len(rows):
                                    i += 1
                                    while i < len(rows):
                                        data_text = rows[i].get_text(strip=True).lower()
                                        if 'how to fill' in data_text or 'category wise' in data_text or 'exam district' in data_text or 'interested candidates' in data_text:
                                            i -= 1
                                            break
                                        tds = [td.get_text(separator=' ', strip=True) for td in rows[i].find_all(['td', 'th'])]
                                        if len(tds) >= 3:
                                            post_matrix.append({
                                                "name": tds[0],
                                                "posts": tds[1],
                                                "eligibility": " ".join(tds[2:])
                                            })
                                        i += 1
                                    i += 1
                                    continue
                                    
                            # 2. Category Wise
                            if 'category wise vacancy details' in text:
                                i += 1
                                if i < len(rows):
                                    headers_td = [td.get_text(strip=True) for td in rows[i].find_all(['td', 'th'])]
                                    i += 1
                                    if i < len(rows):
                                        data_tds = [td.get_text(strip=True) for td in rows[i].find_all(['td', 'th'])]
                                        for h, d in zip(headers_td, data_tds):
                                            if h.lower() != 'post name':
                                                category_vacancies[h] = d
                                    i += 1
                                    continue
                                    
                            # 3. How to Fill
                            if 'how to fill' in text and 'online form' in text:
                                td = tr.find(['td', 'th'])
                                if td:
                                    lines = [t.strip() for t in td.stripped_strings if len(t.strip()) > 10 and 'Sarkari Result' not in t]
                                    how_to_fill = lines[1:] if lines else []"""

replace_str = """                            # 1. Post Matrix
                            if ('vacancy details' in text or 'result details' in text or 'admit card' in text or 'exam details' in text) and 'total' in text and 'category wise' not in text:
                                i += 1
                                if i < len(rows):
                                    i += 1
                                    while i < len(rows):
                                        data_text = rows[i].get_text(strip=True).lower()
                                        if 'how to' in data_text or 'category wise' in data_text or 'exam district' in data_text or 'interested candidates' in data_text:
                                            i -= 1
                                            break
                                        tds = [td.get_text(separator=' ', strip=True) for td in rows[i].find_all(['td', 'th'])]
                                        if len(tds) >= 3:
                                            post_matrix.append({
                                                "name": tds[0],
                                                "posts": tds[1],
                                                "eligibility": " ".join(tds[2:])
                                            })
                                        i += 1
                                    i += 1
                                    continue
                                    
                            # 2. Category Wise
                            if 'category wise' in text or 'vacancy details' in text and 'category' in text:
                                i += 1
                                if i < len(rows):
                                    headers_td = [td.get_text(strip=True) for td in rows[i].find_all(['td', 'th'])]
                                    i += 1
                                    if i < len(rows):
                                        data_tds = [td.get_text(strip=True) for td in rows[i].find_all(['td', 'th'])]
                                        for h, d in zip(headers_td, data_tds):
                                            if h.lower() != 'post name':
                                                category_vacancies[h] = d
                                    i += 1
                                    continue
                                    
                            # 3. How to Fill
                            if 'how to' in text and ('fill' in text or 'check' in text or 'download' in text):
                                td = tr.find(['td', 'th'])
                                if td:
                                    lines = [t.strip() for t in td.stripped_strings if len(t.strip()) > 10 and 'Sarkari Result' not in t]
                                    how_to_fill = lines[1:] if lines else []"""

new_code = code.replace(find_str, replace_str)
with open('/root/sarkari-result-portal/fact_checker_agent.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Updated fact_checker_agent.py!")
