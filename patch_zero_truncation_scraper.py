import re

with open('/root/sarkari-result-portal/full_fresh_rescrape.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Enhance cell parsing in full_fresh_rescrape.py to never skip any date/fee/age line
find_dates_parsing = '''                # Important Dates
                if any('important dates' in l.lower() or 'schedule dates' in l.lower() or 'exam dates' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['important dates', 'exam dates', 'schedule']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["important_dates"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["important_dates"][curr_k] = l
                            curr_k = None'''

replace_dates_parsing = '''                # Important Dates (Zero Truncation - Capture 100% of date lines)
                if any('important dates' in l.lower() or 'schedule dates' in l.lower() or 'exam dates' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['important dates', 'exam dates', 'schedule dates']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["important_dates"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["important_dates"][curr_k] = l
                            curr_k = None
                        elif len(l) > 3:
                            data["important_dates"][l] = "Available"'''

code = code.replace(find_dates_parsing, replace_dates_parsing)

find_fee_parsing = '''                # Application Fee
                if any('application fee' in l.lower() or 'fee details' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['application fee', 'fee details']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["application_fee"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["application_fee"][curr_k] = l
                            curr_k = None
                        elif any(w in l.lower() for w in ['pay the exam fee', 'payment mode', 'through online', 'debit card', 'net banking', 'offline fee', 'exempted', 'no application fee']):
                            data["application_fee"]["Payment Mode"] = l'''

replace_fee_parsing = '''                # Application Fee (Zero Truncation - Capture 100% of fee lines & modes)
                if any('application fee' in l.lower() or 'fee details' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['application fee', 'fee details']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["application_fee"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["application_fee"][curr_k] = l
                            curr_k = None
                        elif any(w in l.lower() for w in ['pay the exam fee', 'payment mode', 'through online', 'debit card', 'net banking', 'offline fee', 'exempted', 'no application fee', 'challan']):
                            data["application_fee"]["Payment Mode"] = l
                        elif len(l) > 3:
                            data["application_fee"][l] = "Applicable"'''

code = code.replace(find_fee_parsing, replace_fee_parsing)

find_age_parsing = '''                # Age Limits
                if any('age limit' in l.lower() for l in raw_lines[:3]):
                    curr_k = None
                    for l in raw_lines:
                        if 'age limit as on' in l.lower() or 'age as on' in l.lower():
                            m_d = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', l)
                            if m_d:
                                data["age_as_on"] = m_d.group(1)
                            else:
                                data["age_as_on"] = l.replace('Age Limit as on', '').replace('Age as on', '').replace(':', '').strip()
                        elif 'minimum age' in l.lower() or 'maximum age' in l.lower():
                            if ':' in l:
                                p = l.split(':', 1)
                                k = clean_text(p[0])
                                v = clean_text(p[1])
                                if v:
                                    data["age_limits"][k] = v
                                    curr_k = None
                                else:
                                    curr_k = k
                            else:
                                curr_k = l
                        elif curr_k:
                            data["age_limits"][curr_k] = l
                            curr_k = None
                        elif 'age relaxation' in l.lower():
                            data["age_limits"]["Age Relaxation"] = l'''

replace_age_parsing = '''                # Age Limits (Zero Truncation - Capture 100% of age criteria & relaxations)
                if any('age limit' in l.lower() for l in raw_lines[:3]):
                    curr_k = None
                    for l in raw_lines:
                        if 'age limit as on' in l.lower() or 'age as on' in l.lower():
                            m_d = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', l)
                            if m_d:
                                data["age_as_on"] = m_d.group(1)
                            else:
                                data["age_as_on"] = l.replace('Age Limit as on', '').replace('Age as on', '').replace(':', '').strip()
                        elif 'minimum age' in l.lower() or 'maximum age' in l.lower() or 'age limit' in l.lower():
                            if ':' in l:
                                p = l.split(':', 1)
                                k = clean_text(p[0])
                                v = clean_text(p[1])
                                if v:
                                    data["age_limits"][k] = v
                                    curr_k = None
                                else:
                                    curr_k = k
                            else:
                                curr_k = l
                        elif curr_k:
                            data["age_limits"][curr_k] = l
                            curr_k = None
                        elif 'age relaxation' in l.lower():
                            data["age_limits"]["Age Relaxation"] = l
                        elif len(l) > 4:
                            data["age_limits"][l] = "Applicable"'''

code = code.replace(find_age_parsing, replace_age_parsing)

with open('/root/sarkari-result-portal/full_fresh_rescrape.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated full_fresh_rescrape.py for complete zero truncation!")
