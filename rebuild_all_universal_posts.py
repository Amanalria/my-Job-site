import os
import glob
import re
import json
import datetime
from bs4 import BeautifulSoup
import app

BASE_DIR = "/root/sarkari-result-portal"
PAGES_DIR = os.path.join(BASE_DIR, "pages")
DATA_DIR = os.path.join(BASE_DIR, "data")

STATIC_PAGES = [
    'about-us.html', 'about.html', 'contact.html', 'disclaimer.html',
    'privacy-policy.html', 'terms-and-conditions.html', 'terms.html',
    'index.html', 'admission.html', 'admit-card.html', 'answer-key.html',
    'latest-jobs.html', 'result.html', 'syllabus.html'
]

# 1. Purge all existing post HTML files from pages/
print("Purging all existing post HTML files from pages/...")
deleted_count = 0
for f in os.listdir(PAGES_DIR):
    if f.endswith('.html') and f not in STATIC_PAGES:
        try:
            os.remove(os.path.join(PAGES_DIR, f))
            deleted_count += 1
        except Exception:
            pass
print(f"Deleted {deleted_count} old post HTML files.")

# 2. Read the master universal HTML blueprint
with open(os.path.join(BASE_DIR, 'post_design_preview.html'), 'r', encoding='utf-8') as f:
    MASTER_BLUEPRINT = f.read()

# 3. Define 5 humanized posts for each of the 7 main categories
posts_data = [
    # ==================== LATEST JOBS (5 Posts) ====================
    {
        "slug": "bpsc-school-teacher-tre-4-0-2026",
        "title": "BPSC School Teacher TRE 4.0 Online Form 2026",
        "category": "latest-jobs",
        "post_date": "August 19, 2026",
        "post_time": "11:30 am",
        "short_desc": "Bihar Public Service Commission (BPSC) invites online applications for TRE 4.0 Primary, Middle, Secondary, and Higher Secondary School Teacher vacancies across Bihar schools. Eligible candidates can review vacancy distribution, eligibility criteria, and application procedure below.",
        "start_date": "10 August 2026",
        "last_date": "05 September 2026",
        "fee_last_date": "05 September 2026",
        "exam_date": "October 2026",
        "fee_gen": "₹ 750/-",
        "fee_res": "₹ 200/- (Female & SC / ST / PH)",
        "age_min": "18 Years (Primary) / 21 Years (TGT/PGT)",
        "age_max": "37 Years (Male), 40 Years (Female/OBC)",
        "total_posts": "32,388 Posts",
        "vacancy_rows": [
            ("Primary Teacher (Class 1 to 5)", "11,250", "12th Pass with 50% marks, 2-Year D.El.Ed / B.El.Ed, CTET or BTET Paper 1 qualified."),
            ("Middle School Teacher (Class 6 to 8)", "8,650", "Bachelor Degree with B.Ed or D.El.Ed, CTET or BTET Paper 2 qualified."),
            ("Secondary Teacher TGT (Class 9 to 10)", "7,488", "Graduation / PG with 50% marks, B.Ed and STET Paper 1 qualified."),
            ("Higher Secondary PGT (Class 11 to 12)", "5,000", "Master Degree in concerned subject with 50% marks, B.Ed and STET Paper 2 qualified.")
        ],
        "how_to_apply": [
            "Visit the official BPSC online portal at onlinebpsc.bihar.gov.in.",
            "Complete candidate One Time Registration and log in with your generated credentials.",
            "Fill in educational qualifications and select targeted school teacher cadre.",
            "Upload scanned passport size photograph, signature, and category certificates in prescribed dimensions.",
            "Pay the examination fee online and download the submitted confirmation PDF."
        ],
        "links": [
            ("Apply Online Form", "https://onlinebpsc.bihar.gov.in/", "Click Here"),
            ("Download Official Notification PDF", "https://bpsc.bih.nic.in/", "Click Here"),
            ("BPSC Official Website", "https://bpsc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("What is the last date to apply for BPSC TRE 4.0 Teacher 2026?", "The online application window closes on 05 September 2026."),
            ("What is the qualification required for BPSC Primary Teacher?", "12th pass with D.El.Ed and CTET / BTET Paper 1 qualification.")
        ]
    },
    {
        "slug": "railway-nfr-2026",
        "title": "Railway NFR Apprentice Online Form 2026",
        "category": "latest-jobs",
        "post_date": "August 19, 2026",
        "post_time": "10:11 am",
        "short_desc": "Northeast Frontier Railway (RRC NFR) invites online applications for trade apprentice engagement across diverse mechanical, electrical, and engineering divisions. Selection is based purely on 10th and ITI merit without any written exam.",
        "start_date": "20 July 2026",
        "last_date": "22 August 2026",
        "fee_last_date": "22 August 2026",
        "exam_date": "Merit List Based (No Exam)",
        "fee_gen": "₹ 100/-",
        "fee_res": "₹ 00/- (Exempted for SC / ST / Female)",
        "age_min": "15 Years",
        "age_max": "24 Years as on 01/08/2026",
        "total_posts": "6,777 Posts",
        "vacancy_rows": [
            ("Fitter / Welder / Electrician Apprentice", "3,450", "Class 10th with minimum 50% aggregate and ITI pass certificate in relevant trade."),
            ("Mechanic / Carpenter / Machinist", "2,127", "Class 10th High School with ITI Certificate in corresponding trade."),
            ("Painter / Wireman / Other Technical Trades", "1,200", "Class 10th with minimum 50% marks and ITI certificate from NCVT / SCVT.")
        ],
        "how_to_apply": [
            "Open the official RRC NFR web portal.",
            "Select your designated Railway Division and trade preference.",
            "Enter matriculation percentage and ITI marks accurately.",
            "Upload scanned copies of marksheet, caste certificate, and ID proof.",
            "Submit the processing fee online and save the application receipt."
        ],
        "links": [
            ("Apply Online Form", "https://nfr.indianrailways.gov.in/", "Click Here"),
            ("Download Notification PDF", "https://nfr.indianrailways.gov.in/", "Click Here"),
            ("RRC NFR Official Website", "https://nfr.indianrailways.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Is there an entrance exam for Railway NFR Apprentice?", "No, selection is prepared purely based on merit calculated from 10th and ITI marks.")
        ]
    },
    {
        "slug": "igcar-apprentice-2026",
        "title": "IGCAR Trade Apprentice Online Form 2026",
        "category": "latest-jobs",
        "post_date": "August 19, 2026",
        "post_time": "12:45 pm",
        "short_desc": "Indira Gandhi Centre for Atomic Research (IGCAR) Kalpakkam announces technical trade apprentice engagement for engineering and vocational trade certificate holders.",
        "start_date": "20 July 2026",
        "last_date": "25 August 2026",
        "fee_last_date": "25 August 2026",
        "exam_date": "September 2026",
        "fee_gen": "₹ 00/- (Free)",
        "fee_res": "₹ 00/- (Free for All)",
        "age_min": "18 Years",
        "age_max": "24 Years",
        "total_posts": "198 Posts",
        "vacancy_rows": [
            ("Trade Apprentice (Various Disciplines)", "198", "10th Standard with ITI certificate in Fitter, Turner, Machinist, Electrician, Welder, or Draughtsman.")
        ],
        "how_to_apply": [
            "Register on the national Apprenticeship India portal first.",
            "Navigate to the IGCAR recruitment page and submit applicant profile.",
            "Verify all trade credentials and upload scanned documents.",
            "Submit online application before the scheduled closing date."
        ],
        "links": [
            ("Apply Online Form", "https://www.igcar.gov.in/", "Click Here"),
            ("Download Official Advertisement", "https://www.igcar.gov.in/", "Click Here"),
            ("IGCAR Official Website", "https://www.igcar.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the application fee for IGCAR Apprentice?", "There is zero application fee for all categories.")
        ]
    },
    {
        "slug": "upessc-principal-2026",
        "title": "UPESSC Principal Online Form 2026",
        "category": "latest-jobs",
        "post_date": "August 19, 2026",
        "post_time": "01:15 pm",
        "short_desc": "Uttar Pradesh Education Service Selection Commission (UPESSC) releases recruitment notice for Principal positions in aided intermediate and secondary institutions across Uttar Pradesh.",
        "start_date": "01 August 2026",
        "last_date": "30 August 2026",
        "fee_last_date": "30 August 2026",
        "exam_date": "November 2026",
        "fee_gen": "₹ 1,000/-",
        "fee_res": "₹ 500/- (SC / ST)",
        "age_min": "30 Years",
        "age_max": "62 Years",
        "total_posts": "2,150 Posts",
        "vacancy_rows": [
            ("Principal (Intermediate College)", "1,200", "Post Graduate Degree with minimum 10 years teaching experience in recognised intermediate college."),
            ("Headmaster (High School)", "950", "Post Graduate Degree, B.Ed and minimum 8 years approved teaching experience.")
        ],
        "how_to_apply": [
            "Complete candidate registration on the official UP Education Service portal.",
            "Provide institutional teaching experience details and qualification records.",
            "Upload authenticated service certificates along with identity credentials.",
            "Submit the application fee and retain final submission confirmation."
        ],
        "links": [
            ("Apply Online Form", "https://upseb.org/", "Click Here"),
            ("Download Official Notification", "https://upseb.org/", "Click Here"),
            ("UPESSC Official Website", "https://upseb.org/", "Click Here")
        ],
        "faqs": [
            ("What is the required teaching experience for UP Principal post?", "A minimum of 8 to 10 years recognized school teaching experience is required.")
        ]
    },
    {
        "slug": "ibps-clerk-16th-2026",
        "title": "IBPS Clerk (CSA) 16th Online Form 2026",
        "category": "latest-jobs",
        "post_date": "August 19, 2026",
        "post_time": "02:00 pm",
        "short_desc": "Institute of Banking Personnel Selection (IBPS) announces Common Recruitment Process (CRP CSA XVI) for Customer Service Associates and Clerical cadre across participating public sector banks.",
        "start_date": "05 August 2026",
        "last_date": "28 August 2026",
        "fee_last_date": "28 August 2026",
        "exam_date": "Prelims: Oct 2026 / Mains: Dec 2026",
        "fee_gen": "₹ 850/-",
        "fee_res": "₹ 175/- (SC / ST / PWD)",
        "age_min": "20 Years",
        "age_max": "28 Years as on 01/08/2026",
        "total_posts": "11,403 Posts",
        "vacancy_rows": [
            ("Clerk / Customer Service Associate (CSA)", "11,403", "Bachelor Degree in any stream from a recognized university and computer operating knowledge.")
        ],
        "how_to_apply": [
            "Open IBPS portal, click on CRP Clerical XVI and choose New Registration.",
            "Enter primary personal contact information to generate registration ID and password.",
            "Upload photograph, signature, left thumb impression, and hand-written declaration.",
            "Submit bank preference list and pay the examination fee online."
        ],
        "links": [
            ("Apply Online Registration", "https://ibps.in/", "Click Here"),
            ("Download IBPS Clerk Notification", "https://ibps.in/", "Click Here"),
            ("IBPS Official Website", "https://ibps.in/", "Click Here")
        ],
        "faqs": [
            ("How many vacancies are announced in IBPS Clerk 2026?", "A total of 11,403 clerical posts are open across participating public banks.")
        ]
    },

    # ==================== RESULTS (5 Posts) ====================
    {
        "slug": "csbc-bihar-prohibition-constable-2026",
        "title": "Bihar Police Prohibition Constable Result 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "09:45 am",
        "short_desc": "Central Selection Board of Constable (CSBC) Bihar publishes the written examination results and physical endurance test (PET) qualified list for Prohibition Constable recruitment.",
        "start_date": "Exam Date: June 2026",
        "last_date": "Result: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "PET: September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years",
        "total_posts": "1,280 Posts",
        "vacancy_rows": [
            ("Prohibition Constable (Madh Nishedh)", "1,280", "Written test qualified candidates shortlisted for Physical Efficiency Test (PET).")
        ],
        "how_to_apply": [
            "Visit CSBC Bihar official website at csbc.bih.nic.in.",
            "Click on Prohibition Dept section on the main dashboard.",
            "Open the Result notification PDF for Prohibition Constable recruitment.",
            "Search candidate Roll Number inside the PDF."
        ],
        "links": [
            ("Download Result PDF", "https://csbc.bih.nic.in/", "Click Here"),
            ("Check Cutoff Marks Notice", "https://csbc.bih.nic.in/", "Click Here"),
            ("CSBC Official Website", "https://csbc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("How can I check my Bihar Prohibition Constable result?", "Download the official selection list PDF and search using your assigned roll number.")
        ]
    },
    {
        "slug": "bihar-police-csbc-constable-operator-2026",
        "title": "Bihar Police CSBC Constable Operator Result 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "10:30 am",
        "short_desc": "CSBC Bihar releases scorecards and shortlisted candidate rolls for Bihar Police Wireless Operator and Technical Constable recruitment examination.",
        "start_date": "Exam Date: May 2026",
        "last_date": "Result: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Skill Test: September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years",
        "total_posts": "980 Posts",
        "vacancy_rows": [
            ("Constable Wireless Operator", "980", "Written examination qualified for physical standards and technical skill test.")
        ],
        "how_to_apply": [
            "Open the CSBC Bihar portal homepage.",
            "Select the Bihar Police Wireless division tab.",
            "Click on the scorecard and result link.",
            "Enter candidate Roll Number and Date of Birth to view qualifying score."
        ],
        "links": [
            ("Download Operator Result", "https://csbc.bih.nic.in/", "Click Here"),
            ("CSBC Official Website", "https://csbc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("Where is the CSBC operator merit list published?", "The merit list is hosted directly on the CSBC official portal at csbc.bih.nic.in.")
        ]
    },
    {
        "slug": "bihar-police-csbc-constable-2026",
        "title": "Bihar Police CSBC Constable GD Result 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "11:00 am",
        "short_desc": "Central Selection Board of Constable publishes the comprehensive list of candidates qualified in Bihar Police GD Constable written examination for PET evaluation.",
        "start_date": "Written Exam: July 2026",
        "last_date": "Result: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Physical Test: Sept-Oct 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years",
        "total_posts": "21,391 Posts",
        "vacancy_rows": [
            ("Constable GD (General Duty)", "21,391", "Shortlisted for Physical Efficiency Test (PET), running, high jump, and shot put.")
        ],
        "how_to_apply": [
            "Visit the official website of CSBC Bihar.",
            "Download the official Constable GD Result document.",
            "Search candidate Roll Number within the shortlisted roll matrix.",
            "Keep the result printout safe for document verification at the PET venue."
        ],
        "links": [
            ("Download GD Result PDF", "https://csbc.bih.nic.in/", "Click Here"),
            ("Check PET Guidelines", "https://csbc.bih.nic.in/", "Click Here"),
            ("CSBC Official Website", "https://csbc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("What is the next stage after Bihar Police Constable written result?", "Qualified aspirants will appear for the physical efficiency examination (PET).")
        ]
    },
    {
        "slug": "kvs-nvs-teaching-non-teaching-2026",
        "title": "KVS NVS Teaching & Non-Teaching Tier-II Result 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "11:45 am",
        "short_desc": "Kendriya Vidyalaya Sangathan (KVS) and Navodaya Vidyalaya Samiti (NVS) release combined Tier-II written examination results and interview shortlist.",
        "start_date": "Tier-II Exam: May 2026",
        "last_date": "Result Declared: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Interviews: September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "35-40 Years",
        "total_posts": "13,400 Posts",
        "vacancy_rows": [
            ("TGT, PGT & PRT Teaching Posts", "9,800", "Shortlisted for document verification and personal interview round."),
            ("Non-Teaching Administrative Posts", "3,600", "Shortlisted for skill evaluation and typing test.")
        ],
        "how_to_apply": [
            "Visit the official KVS recruitment portal at kvsangathan.nic.in.",
            "Open the Employment Notice tab and click on Tier-II Result link.",
            "Download post-wise PDF containing shortlisted candidate rolls.",
            "Verify your interview slot date and reporting centre address."
        ],
        "links": [
            ("Download KVS NVS Result", "https://kvsangathan.nic.in/", "Click Here"),
            ("KVS Official Website", "https://kvsangathan.nic.in/", "Click Here")
        ],
        "faqs": [
            ("When will KVS Tier-II interview rounds commence?", "Interviews are scheduled starting from the second week of September 2026.")
        ]
    },
    {
        "slug": "upsssc-vdo-2023",
        "title": "UPSSSC VDO 2023 Final Result & Cutoff",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "12:15 pm",
        "short_desc": "Uttar Pradesh Subordinate Services Selection Commission (UPSSSC) declares the final selection result and category-wise cutoff marks for Village Development Officer (Gram Vikas Adhikari) examination.",
        "start_date": "Re-Exam: June 2023",
        "last_date": "Final Result: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Joining Notice: Sept 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "40 Years",
        "total_posts": "1,953 Posts",
        "vacancy_rows": [
            ("Gram Vikas Adhikari (VDO)", "1,526", "Final recommended candidate list for district allotment."),
            ("Gram Panchayat Adhikari & Samaj Kalyan", "427", "Final recommended candidate merit list.")
        ],
        "how_to_apply": [
            "Access the official UPSSSC website at upsssc.gov.in.",
            "Click on the Notice Board section on the homepage.",
            "Download the Final Recommendation List for Advt 02-Exam/2018.",
            "Verify roll number, category cutoff score, and document clearance status."
        ],
        "links": [
            ("Download Final Result & Cutoff PDF", "http://upsssc.gov.in/", "Click Here"),
            ("UPSSSC Official Website", "http://upsssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How to check UPSSSC VDO final cutoff marks?", "The detailed category cutoff breakdown is available in the official result notification PDF.")
        ]
    },

    # ==================== ADMIT CARDS (5 Posts) ====================
    {
        "slug": "upsssc-lower-pcs-2026",
        "title": "UPSSSC Lower PCS Admit Card 2026",
        "category": "admit-card",
        "post_date": "August 19, 2026",
        "post_time": "08:30 am",
        "short_desc": "UPSSSC releases the preliminary examination admit cards and exam city information slips for Lower Subordinate Services recruitment examination.",
        "start_date": "Admit Card: August 2026",
        "last_date": "Exam Date: September 2026",
        "fee_last_date": "N/A",
        "exam_date": "14-15 September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "21 Years",
        "age_max": "40 Years",
        "total_posts": "672 Posts",
        "vacancy_rows": [
            ("Lower Subordinate Services (Various Posts)", "672", "Download hall ticket using candidate registration number and date of birth.")
        ],
        "how_to_apply": [
            "Open the official UPSSSC examination portal.",
            "Click on Download Admit Card for Examination 2026 link.",
            "Enter candidate Registration Number, Date of Birth, and Gender.",
            "Enter verification captcha code and click Download Admit Card.",
            "Print the hall ticket in clear format along with valid ID guidelines."
        ],
        "links": [
            ("Download Admit Card", "http://upsssc.gov.in/", "Click Here"),
            ("Check Exam City Slip", "http://upsssc.gov.in/", "Click Here"),
            ("UPSSSC Official Website", "http://upsssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What details are required to download UPSSSC Lower PCS admit card?", "You need your registration number, date of birth, gender, and security captcha.")
        ]
    },
    {
        "slug": "bsf-hcm-asi-steno-2025",
        "title": "BSF HCM & ASI Steno Admit Card 2026",
        "category": "admit-card",
        "post_date": "August 19, 2026",
        "post_time": "09:15 am",
        "short_desc": "Border Security Force (BSF) publishes the Computer Based Written Examination (CBT) admit cards for Head Constable Ministerial and Assistant Sub Inspector Steno posts.",
        "start_date": "Admit Card: August 2026",
        "last_date": "Exam Date: September 2026",
        "fee_last_date": "N/A",
        "exam_date": "20 September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years",
        "total_posts": "1,526 Posts",
        "vacancy_rows": [
            ("Head Constable (Ministerial)", "1,283", "CBT Examination call letter issued for eligible applicants."),
            ("ASI (Stenographer)", "243", "CBT Examination call letter issued.")
        ],
        "how_to_apply": [
            "Visit the official BSF recruitment website at rectt.bsf.gov.in.",
            "Log in using your registered Email ID and Password.",
            "Click on Action menu and select Download Hall Ticket.",
            "Print the examination admit card along with essential self-declaration form."
        ],
        "links": [
            ("Download BSF Admit Card", "https://rectt.bsf.gov.in/", "Click Here"),
            ("BSF Official Website", "https://rectt.bsf.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Which documents must be carried to the BSF exam centre?", "Carry printed admit card, two passport photos, and an original government photo ID.")
        ]
    },
    {
        "slug": "cci-various-post-2026",
        "title": "Cotton Corporation of India CCI Exam City Details 2026",
        "category": "admit-card",
        "post_date": "August 19, 2026",
        "post_time": "10:00 am",
        "short_desc": "Cotton Corporation of India Limited (CCIL) activates exam city intimation slip and admit card download portal for Management Trainee, Junior Commercial Executive and Junior Assistant posts.",
        "start_date": "City Intimation: August 2026",
        "last_date": "Exam Date: September 2026",
        "fee_last_date": "N/A",
        "exam_date": "18 September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "30 Years",
        "total_posts": "214 Posts",
        "vacancy_rows": [
            ("Junior Commercial Executive & Other Posts", "214", "Check allocated exam city and download e-admit card.")
        ],
        "how_to_apply": [
            "Visit the official CCIL careers page.",
            "Enter candidate Application Reference Number and Date of Birth.",
            "Check exam city, test shift timing, and reporting instructions.",
            "Download and take a printout of the admit card."
        ],
        "links": [
            ("Check Exam City Details", "https://cotcorp.org.in/", "Click Here"),
            ("CCI Official Website", "https://cotcorp.org.in/", "Click Here")
        ],
        "faqs": [
            ("When will CCI admit card be released?", "Exam city details are live now and admit card downloads are enabled.")
        ]
    },
    {
        "slug": "nta-aiapget-2026",
        "title": "NTA AIAPGET Admit Card 2026",
        "category": "admit-card",
        "post_date": "August 19, 2026",
        "post_time": "10:45 am",
        "short_desc": "National Testing Agency (NTA) issues the All India Ayush Post Graduate Entrance Test (AIAPGET 2026) admit cards for Ayurveda, Unani, Siddha & Homeopathy MD/MS courses.",
        "start_date": "Admit Card: August 2026",
        "last_date": "Exam Date: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "29 August 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "No Upper Age Limit",
        "age_max": "No Upper Age Limit",
        "total_posts": "AYUSH PG Admission 2026",
        "vacancy_rows": [
            ("AIAPGET Ayush MD / MS Entrance", "All India PG Seats", "BAMS / BUMS / BSMS / BHMS degree holders with completed internship.")
        ],
        "how_to_apply": [
            "Open the official AIAPGET NTA website at exams.nta.ac.in/AIAPGET.",
            "Click on the Admit Card Login link.",
            "Enter candidate Application Number and Date of Birth.",
            "Download the admit card PDF and review test center address carefully."
        ],
        "links": [
            ("Download AIAPGET Admit Card", "https://exams.nta.ac.in/", "Click Here"),
            ("NTA Official Website", "https://exams.nta.ac.in/", "Click Here")
        ],
        "faqs": [
            ("Who conducts AIAPGET 2026 examination?", "National Testing Agency (NTA) on behalf of Ministry of Ayush.")
        ]
    },
    {
        "slug": "nbems-various-post-2026",
        "title": "NBEMS Group A, B & C Exam City Details 2026",
        "category": "admit-card",
        "post_date": "August 19, 2026",
        "post_time": "11:15 am",
        "short_desc": "National Board of Examinations in Medical Sciences (NBEMS) releases advance exam city intimation slip and hall tickets for Junior Assistant, Senior Assistant, and Accountant recruitment.",
        "start_date": "City Slip: August 2026",
        "last_date": "Exam: September 2026",
        "fee_last_date": "N/A",
        "exam_date": "10 September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "27 Years",
        "total_posts": "85 Posts",
        "vacancy_rows": [
            ("Senior Assistant & Junior Assistant", "85", "Download hall ticket using candidate user ID and password.")
        ],
        "how_to_apply": [
            "Visit natboard.edu.in recruitment section.",
            "Click on Candidate Login for Group A, B, C Examination.",
            "Download your allotted examination city slip and admit card."
        ],
        "links": [
            ("Check NBEMS Exam City", "https://natboard.edu.in/", "Click Here"),
            ("NBEMS Official Website", "https://natboard.edu.in/", "Click Here")
        ],
        "faqs": [
            ("What is the exam date for NBEMS Junior Assistant?", "The computer-based test is scheduled for 10 September 2026.")
        ]
    },

    # ==================== ANSWER KEY (5 Posts) ====================
    {
        "slug": "nta-icar-aieea-pg-and-phd-2026",
        "title": "NTA ICAR AIEEA PG Ph.D Answer Key 2026",
        "category": "answer-key",
        "post_date": "August 19, 2026",
        "post_time": "09:00 am",
        "short_desc": "National Testing Agency (NTA) issues the provisional answer keys and candidate response sheets for Indian Council of Agricultural Research (ICAR) AIEEA PG and AICE JRF/SRF Ph.D entrance examinations.",
        "start_date": "Key Released: August 2026",
        "last_date": "Objection Window: 24 August 2026",
        "fee_last_date": "24 August 2026",
        "exam_date": "Exam Held: July 2026",
        "fee_gen": "₹ 200/- per challenge",
        "fee_res": "₹ 200/- per challenge",
        "age_min": "19 Years (PG)",
        "age_max": "No Upper Age Limit",
        "total_posts": "ICAR PG & PhD Admission",
        "vacancy_rows": [
            ("ICAR AIEEA PG & AICE PhD Answer Key", "All India Agriculture Seats", "Candidates can match response sheet and raise online objections.")
        ],
        "how_to_apply": [
            "Navigate to the official ICAR NTA website at exams.nta.ac.in/ICAR.",
            "Click on Answer Key Challenge link.",
            "Login with Application Number and Password or Date of Birth.",
            "View candidate response sheet alongside provisional master answer key.",
            "Submit objections if any with documentary proof by paying challenge fee."
        ],
        "links": [
            ("Download ICAR Answer Key & Response Sheet", "https://exams.nta.ac.in/", "Click Here"),
            ("NTA ICAR Official Website", "https://exams.nta.ac.in/", "Click Here")
        ],
        "faqs": [
            ("What is the fee to challenge an NTA ICAR answer key question?", "A non-refundable processing fee of Rs. 200 is required per challenged question.")
        ]
    },
    {
        "slug": "nta-csir-ugc-net-june-2026",
        "title": "NTA CSIR UGC NET June Answer Key 2026",
        "category": "answer-key",
        "post_date": "August 19, 2026",
        "post_time": "09:30 am",
        "short_desc": "NTA publishes the official provisional answer keys and recorded responses for the Joint CSIR UGC NET June examination across chemical, earth, life, mathematical, and physical sciences.",
        "start_date": "Key Out: August 2026",
        "last_date": "Objection Window: 25 August 2026",
        "fee_last_date": "25 August 2026",
        "exam_date": "Exam Held: July 2026",
        "fee_gen": "₹ 200/- per question",
        "fee_res": "₹ 200/- per question",
        "age_min": "No Limit (Lectureship) / 28 Years (JRF)",
        "age_max": "Age relaxation as per norms",
        "total_posts": "JRF & Assistant Professor Eligibility",
        "vacancy_rows": [
            ("CSIR UGC NET June (5 Science Streams)", "National Level Eligibility", "Download master question paper and candidate response sheet.")
        ],
        "how_to_apply": [
            "Visit the CSIR NET portal at csirnet.nta.ac.in.",
            "Log in using Application Number and Date of Birth.",
            "Download your answer sheet and verify correct answer keys.",
            "File challenges online if you notice any discrepancy."
        ],
        "links": [
            ("Download CSIR NET Answer Key", "https://csirnet.nta.ac.in/", "Click Here"),
            ("CSIR NTA Official Website", "https://csirnet.nta.ac.in/", "Click Here")
        ],
        "faqs": [
            ("How to challenge CSIR NET answer key?", "Log in to the NTA portal, select question ID, provide justification and complete online fee payment.")
        ]
    },
    {
        "slug": "bpsc-apo-2026",
        "title": "Bihar BPSC Assistant Prosecution Officer APO Answer Key 2026",
        "category": "answer-key",
        "post_date": "August 19, 2026",
        "post_time": "10:15 am",
        "short_desc": "Bihar Public Service Commission (BPSC) releases provisional answer keys for General Studies and Law papers in the Assistant Prosecution Officer preliminary test.",
        "start_date": "Key Released: August 2026",
        "last_date": "Objection Deadline: 26 August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Exam Held: August 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "21 Years",
        "age_max": "37 Years (Male), 40 Years (Female)",
        "total_posts": "553 Posts",
        "vacancy_rows": [
            ("Assistant Prosecution Officer (APO)", "553", "Check question booklet series A, B, C, D answer keys.")
        ],
        "how_to_apply": [
            "Go to bpsc.bih.nic.in homepage.",
            "Click on Provisional Answer Key for General Studies & Law Booklet.",
            "Compare your marked answers with the official key PDF.",
            "Submit objection format via speed post to BPSC office if needed."
        ],
        "links": [
            ("Download BPSC APO Answer Key PDF", "https://bpsc.bih.nic.in/", "Click Here"),
            ("BPSC Official Website", "https://bpsc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("Where can I download BPSC APO answer keys?", "Directly from the BPSC official website at bpsc.bih.nic.in.")
        ]
    },
    {
        "slug": "upsssc-agriculture-technical-assistant-group-c-2026",
        "title": "UPSSSC Agriculture Technical Assistant Group-C Answer Key 2026",
        "category": "answer-key",
        "post_date": "August 19, 2026",
        "post_time": "11:00 am",
        "short_desc": "UPSSSC publishes provisional answer keys for Agriculture Technical Assistant (Pravidhik Sahayak Group C) examination.",
        "start_date": "Key Out: August 2026",
        "last_date": "Objection Date: 28 August 2026",
        "fee_last_date": "28 August 2026",
        "exam_date": "Exam Held: August 2026",
        "fee_gen": "₹ 100/- per challenge",
        "fee_res": "₹ 100/- per challenge",
        "age_min": "21 Years",
        "age_max": "40 Years",
        "total_posts": "3,446 Posts",
        "vacancy_rows": [
            ("Krishi Pravidhik Sahayak Group-C", "3,446", "Download question booklet master key and response sheet.")
        ],
        "how_to_apply": [
            "Visit upsssc.gov.in and click on View Provisional Answer Key.",
            "Log in with candidate credentials to view answer key.",
            "Submit challenges online through the candidate objection tracking portal."
        ],
        "links": [
            ("Download AGTA Answer Key", "http://upsssc.gov.in/", "Click Here"),
            ("UPSSSC Official Website", "http://upsssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How many posts are available in UPSSSC Agriculture Technical Assistant?", "3,446 Group-C positions are being filled.")
        ]
    },
    {
        "slug": "dsssb-various-post-2026",
        "title": "Delhi DSSSB Various Post Answer Key 2026",
        "category": "answer-key",
        "post_date": "August 19, 2026",
        "post_time": "11:30 am",
        "short_desc": "Delhi Subordinate Services Selection Board (DSSSB) releases draft answer keys and objection link for computer-based tests conducted for various teaching, technical, and ministerial posts.",
        "start_date": "Key Out: August 2026",
        "last_date": "Objection Last Date: 27 August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Exam Held: July-August 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "27-32 Years",
        "total_posts": "4,198 Posts",
        "vacancy_rows": [
            ("DSSSB Teaching & Non-Teaching Posts", "4,198", "Login to view response sheet and submit draft key objections.")
        ],
        "how_to_apply": [
            "Visit dsssb.delhi.gov.in.",
            "Click on Objection Management Link for CBT Examinations.",
            "Log in using Application Number and Date of Birth.",
            "Review response sheet and submit challenge if applicable."
        ],
        "links": [
            ("Download DSSSB Answer Key", "https://dsssb.delhi.gov.in/", "Click Here"),
            ("DSSSB Official Website", "https://dsssb.delhi.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How to log in to DSSSB objection management portal?", "Enter your application number and date of birth in DD/MM/YYYY format.")
        ]
    },

    # ==================== DOCUMENTS & SYLLABUS (5 Posts) ====================
    {
        "slug": "bpsc-exam-calendar-2026",
        "title": "BPSC Annual Examination Calendar 2026",
        "category": "syllabus",
        "post_date": "August 19, 2026",
        "post_time": "08:15 am",
        "short_desc": "Bihar Public Service Commission (BPSC) releases the official updated examination calendar outlining test dates, mains schedules, and result declaration timelines for 2026-27 recruitments.",
        "start_date": "Calendar Out: August 2026",
        "last_date": "Valid For: 2026-2027",
        "fee_last_date": "N/A",
        "exam_date": "As per Schedule",
        "fee_gen": "Nil (Free Download)",
        "fee_res": "Nil (Free Download)",
        "age_min": "N/A",
        "age_max": "N/A",
        "total_posts": "State Level Annual Calendar",
        "vacancy_rows": [
            ("70th & 71st BPSC CCE Combined Exam", "Prelims & Mains", "Check scheduled preliminary, mains, and interview tentative windows."),
            ("TRE 4.0 & TRE 5.0 Teacher Recruitment", "Teacher Exams", "Check annual schedule for Bihar teacher recruitment tests."),
            ("Assistant Engineer, Medical Officer & Judicial", "Technical Services", "Check dates for departmental examinations.")
        ],
        "how_to_apply": [
            "Visit the official BPSC portal at bpsc.bih.nic.in.",
            "Look for the BPSC Examination Calendar 2026-2027 link on the homepage.",
            "Download the PDF and check specific notification dates for your targeted post.",
            "Plan your exam preparation strategy according to official test timelines."
        ],
        "links": [
            ("Download BPSC Exam Calendar PDF", "https://bpsc.bih.nic.in/", "Click Here"),
            ("BPSC Official Website", "https://bpsc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("When will BPSC 71st Prelims be conducted as per calendar?", "Please check the exact month specified in the official PDF schedule.")
        ]
    },
    {
        "slug": "delhi-laxmi-yojana-2026",
        "title": "Delhi Laxmi Yojana Online Application Form 2026",
        "category": "syllabus",
        "post_date": "August 19, 2026",
        "post_time": "08:45 am",
        "short_desc": "Government of NCT Delhi announces financial empowerment and educational support scheme guidelines for girl children and women across the capital city.",
        "start_date": "Scheme Open: August 2026",
        "last_date": "Ongoing Application",
        "fee_last_date": "N/A",
        "exam_date": "Direct Benefit Transfer",
        "fee_gen": "Nil (Free Scheme)",
        "fee_res": "Nil (Free Scheme)",
        "age_min": "Delhi Resident",
        "age_max": "Eligible Family Members",
        "total_posts": "Financial Support Scheme",
        "vacancy_rows": [
            ("Delhi Laxmi Yojana Welfare Grant", "Direct DBT", "Valid Delhi domicile certificate, Aadhaar card, income certificate and active bank account.")
        ],
        "how_to_apply": [
            "Visit the Delhi government e-district welfare portal.",
            "Register using Aadhaar credentials and complete citizen profile.",
            "Fill in beneficiary information and bank account details.",
            "Upload proof of residence, family income certificate, and submit form."
        ],
        "links": [
            ("Apply Online on e-District", "https://edistrict.delhigovt.nic.in/", "Click Here"),
            ("Download Scheme Guidelines PDF", "https://delhi.gov.in/", "Click Here"),
            ("Delhi Govt Official Website", "https://delhi.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Who is eligible for Delhi Laxmi Yojana?", "Permanent residents of Delhi meeting family income criteria are eligible.")
        ]
    },
    {
        "slug": "up-scholarship-2026",
        "title": "UP Pre & Post Matric Scholarship Online Form 2026-27",
        "category": "syllabus",
        "post_date": "August 19, 2026",
        "post_time": "09:20 am",
        "short_desc": "Social Welfare Department, Government of Uttar Pradesh opens student scholarship registration for Pre-Matric (Class 9-10) and Post-Matric (Class 11-12, UG, PG, Diploma) courses.",
        "start_date": "01 July 2026",
        "last_date": "31 October 2026",
        "fee_last_date": "N/A",
        "exam_date": "Direct DBT to Bank Account",
        "fee_gen": "₹ 00/- (Free)",
        "fee_res": "₹ 00/- (Free for All)",
        "age_min": "Enrolled Student in UP",
        "age_max": "As per Course Norms",
        "total_posts": "UP State Scholarship 2026-27",
        "vacancy_rows": [
            ("Pre-Matric Scholarship (Class 9th & 10th)", "All Eligible Students", "Passed previous class and studying in Class 9 or 10 in a recognized UP institution."),
            ("Post-Matric Intermediate (Class 11th & 12th)", "All Eligible Students", "Enrolled in Class 11 or 12 in recognized board schools in UP."),
            ("Post-Matric Other Than Inter (UG/PG/Diploma)", "All Eligible Students", "Enrolled in Degree, Diploma, ITI, B.Ed, Engineering, or Master degree courses.")
        ],
        "how_to_apply": [
            "Open the official UP Scholarship portal at scholarship.up.gov.in.",
            "Choose Student > Registration and select your respective student category.",
            "Authenticate using Aadhaar biometric/OTP and complete student registration.",
            "Fill academic details, upload marksheets, caste and income certificate numbers.",
            "Submit form and verify details at your educational institution."
        ],
        "links": [
            ("Apply Online Registration", "https://scholarship.up.gov.in/", "Click Here"),
            ("Student Login Portal", "https://scholarship.up.gov.in/", "Click Here"),
            ("UP Scholarship Official Website", "https://scholarship.up.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the last date to submit UP Scholarship online form?", "The portal remains open until 31 October 2026 for post-matric categories.")
        ]
    },
    {
        "slug": "uppsc-exam-calendar-2026",
        "title": "UPPSC Combined Exam Calendar 2026",
        "category": "syllabus",
        "post_date": "August 19, 2026",
        "post_time": "10:10 am",
        "short_desc": "Uttar Pradesh Public Service Commission (UPPSC) publishes the revised annual calendar for Combined State / Upper Subordinate Services (PCS), RO / ARO, and Staff Nurse recruitments.",
        "start_date": "Calendar Out: August 2026",
        "last_date": "Valid For: 2026-2027",
        "fee_last_date": "N/A",
        "exam_date": "As per Schedule",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "N/A",
        "age_max": "N/A",
        "total_posts": "UP State Level Examinations",
        "vacancy_rows": [
            ("UPPSC PCS Prelims & Mains Exam", "PCS 2026", "Check designated test dates for preliminary and descriptive main papers."),
            ("Review Officer / Assistant Review Officer (RO/ARO)", "RO/ARO Exam", "Check rescheduled examination dates."),
            ("Staff Nurse, Lecturer & Combined Technical", "Specialized Posts", "Check scheduled test slots.")
        ],
        "how_to_apply": [
            "Visit uppsc.up.nic.in homepage.",
            "Click on All Notifications / Advertisements and select Examination Calendar.",
            "Download PDF document and review the chronological test dates."
        ],
        "links": [
            ("Download UPPSC Calendar PDF", "https://uppsc.up.nic.in/", "Click Here"),
            ("UPPSC Official Website", "https://uppsc.up.nic.in/", "Click Here")
        ],
        "faqs": [
            ("Where can I verify UPPSC exam schedule?", "Official updates are published exclusively at uppsc.up.nic.in.")
        ]
    },
    {
        "slug": "ssc-exam-calendar-2026-27",
        "title": "Staff Selection Commission SSC Revised Calendar 2026-27",
        "category": "syllabus",
        "post_date": "August 19, 2026",
        "post_time": "11:20 am",
        "short_desc": "Staff Selection Commission (SSC) releases the updated annual examination planner specifying notification release dates, application windows, and computer-based test slots for CGL, CHSL, MTS, GD Constable, and CPO examinations.",
        "start_date": "Calendar Out: August 2026",
        "last_date": "Valid for: 2026-2027",
        "fee_last_date": "N/A",
        "exam_date": "Monthly Computer-Based Tests",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "32 Years",
        "total_posts": "All India SSC Recruitments",
        "vacancy_rows": [
            ("SSC CGL (Combined Graduate Level)", "Tier 1 & Tier 2", "Bachelor degree holders. Check official notification and test schedule."),
            ("SSC CHSL (10+2 Higher Secondary Level)", "Tier 1 & Tier 2", "12th standard pass candidates. Check application and test dates."),
            ("SSC GD Constable & MTS (Multi Tasking)", "CBT Examinations", "10th pass candidates. Check computer based exam windows.")
        ],
        "how_to_apply": [
            "Access the new SSC official web portal at ssc.gov.in.",
            "Click on the Notice Board section on the main page.",
            "Download the Revised Annual Calendar PDF.",
            "Note down key notification release dates and plan preparation accordingly."
        ],
        "links": [
            ("Download SSC Calendar PDF", "https://ssc.gov.in/", "Click Here"),
            ("SSC Official Website", "https://ssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the official website for SSC exam updates?", "The official portal is ssc.gov.in.")
        ]
    },

    # ==================== ADMISSION (5 Posts) ====================
    {
        "slug": "iit-jam-2027",
        "title": "IIT JAM 2027 Online Form",
        "category": "admission",
        "post_date": "August 19, 2026",
        "post_time": "08:10 am",
        "short_desc": "Indian Institute of Technology (IIT) invites online applications for Joint Admission Test for Masters (JAM 2027) for admission to M.Sc., Joint M.Sc.-Ph.D., M.Sc.-Ph.D. Dual Degree, and integrated postgraduate science programs across premier IITs and IISc.",
        "start_date": "03 September 2026",
        "last_date": "11 October 2026",
        "fee_last_date": "11 October 2026",
        "exam_date": "08 February 2027",
        "fee_gen": "₹ 1,800/- (One Test) / ₹ 2,500/- (Two)",
        "fee_res": "₹ 900/- (Female / SC / ST / PwD)",
        "age_min": "No Age Limit",
        "age_max": "No Age Limit",
        "total_posts": "IIT M.Sc. Postgraduate Admissions",
        "vacancy_rows": [
            ("M.Sc. / Joint M.Sc.-Ph.D. Programs", "All Premier IITs", "Bachelor degree in science / mathematics or appearing in final qualifying year.")
        ],
        "how_to_apply": [
            "Open the official JOAPS portal.",
            "Create candidate login by registering name, valid email, and mobile number.",
            "Enter academic qualification details and choose your test paper subjects.",
            "Upload photograph, signature, and category certificate according to prescribed dimensions.",
            "Pay the examination fee online and download confirmation page."
        ],
        "links": [
            ("Apply Online JOAPS Portal", "https://jam2027.iit.ac.in/", "Click Here"),
            ("Download Information Brochure", "https://jam2027.iit.ac.in/", "Click Here"),
            ("IIT JAM Official Website", "https://jam2027.iit.ac.in/", "Click Here")
        ],
        "faqs": [
            ("When will IIT JAM 2027 examination be conducted?", "The national entrance exam will be held on 08 February 2027 across multiple shifts.")
        ]
    },
    {
        "slug": "sav-bihar-class-6-2026",
        "title": "SAV Bihar Class 6 Entrance Exam Online Form 2027-28",
        "category": "admission",
        "post_date": "August 19, 2026",
        "post_time": "08:50 am",
        "short_desc": "Bihar School Examination Board (BSEB) invites online applications for entrance admission to Class VI in Simultala Awasiya Vidyalaya (SAV) Jamui for academic session 2027-28.",
        "start_date": "10 July 2026",
        "last_date": "28 August 2026 (Extended)",
        "fee_last_date": "28 August 2026",
        "exam_date": "October 2026",
        "fee_gen": "₹ 200/-",
        "fee_res": "₹ 50/- (SC / ST)",
        "age_min": "10 Years as on 01/04/2027",
        "age_max": "12 Years as on 01/04/2027",
        "total_posts": "120 Seats (60 Boys + 60 Girls)",
        "vacancy_rows": [
            ("Simultala Class 6 Residential Admission", "120 Seats", "Student currently studying in Class 5 in a recognized school in Bihar.")
        ],
        "how_to_apply": [
            "Visit secondary.biharboardonline.com portal.",
            "Register applicant with student name, parent details, and residential proof.",
            "Upload photo, signature, and Class 5 school study certificate.",
            "Submit application fee online and print acknowledgment receipt."
        ],
        "links": [
            ("Apply Online Registration", "http://secondary.biharboardonline.com/", "Click Here"),
            ("Download Date Extension Notice", "http://secondary.biharboardonline.com/", "Click Here"),
            ("BSEB Official Website", "http://secondary.biharboardonline.com/", "Click Here")
        ],
        "faqs": [
            ("What is the seat capacity for SAV Bihar Class 6 admission?", "A total of 120 residential seats (60 for boys and 60 for girls) are available.")
        ]
    },
    {
        "slug": "bihar-stet-2026",
        "title": "Bihar Secondary Teachers Eligibility Test STET 2026",
        "category": "admission",
        "post_date": "August 19, 2026",
        "post_time": "09:40 am",
        "short_desc": "Bihar School Examination Board (BSEB) invites online applications for Bihar Secondary Teachers Eligibility Test (STET 2026) for qualifying prospective Paper 1 (Secondary 9-10) and Paper 2 (Higher Secondary 11-12) teachers.",
        "start_date": "08 August 2026",
        "last_date": "31 August 2026",
        "fee_last_date": "31 August 2026",
        "exam_date": "September-October 2026",
        "fee_gen": "Single: ₹ 960/- / Both: ₹ 1,440/-",
        "fee_res": "Single: ₹ 760/- / Both: ₹ 1,140/- (SC/ST/PH)",
        "age_min": "21 Years",
        "age_max": "37 Years (Male), 40 Years (Female/BC/EBC)",
        "total_posts": "State Teacher Eligibility Examination",
        "vacancy_rows": [
            ("STET Paper 1 (Class 9 to 10)", "Secondary Level", "Bachelor / Master Degree in relevant subject with minimum 50% marks and B.Ed degree."),
            ("STET Paper 2 (Class 11 to 12)", "Senior Secondary Level", "Master Degree in related subject with 50% marks and B.Ed / B.A.B.Ed degree.")
        ],
        "how_to_apply": [
            "Access the official BSEB STET web portal.",
            "Register as a new user by providing mobile number and email ID.",
            "Select your targeted subject and paper level.",
            "Upload educational certificates, passport photo, and signature.",
            "Complete examination fee payment and save the confirmation PDF."
        ],
        "links": [
            ("Apply Online Registration", "https://bsebstet.com/", "Click Here"),
            ("Download STET Notification PDF", "https://bsebstet.com/", "Click Here"),
            ("BSEB STET Official Website", "https://bsebstet.com/", "Click Here")
        ],
        "faqs": [
            ("Is STET certificate valid for lifetime in Bihar?", "Yes, BSEB STET qualifying certificates possess lifetime validity.")
        ]
    },
    {
        "slug": "iit-gate-2027",
        "title": "IIT GATE 2027 Online Form",
        "category": "admission",
        "post_date": "August 19, 2026",
        "post_time": "10:30 am",
        "short_desc": "Organizing Institute of Technology invites online applications for Graduate Aptitude Test in Engineering (GATE 2027) for M.Tech/Ph.D admissions and recruitment in premier Public Sector Undertakings (PSUs).",
        "start_date": "24 August 2026",
        "last_date": "26 September 2026",
        "fee_last_date": "26 September 2026",
        "exam_date": "06-07 & 13-14 February 2027",
        "fee_gen": "₹ 1,800/- per paper",
        "fee_res": "₹ 900/- (Female / SC / ST / PwD)",
        "age_min": "No Age Limit",
        "age_max": "No Age Limit",
        "total_posts": "M.Tech Admissions & PSU Recruitment",
        "vacancy_rows": [
            ("GATE 2027 Engineering & Science Papers", "All India PG Admissions", "B.E. / B.Tech / B.Pharm / B.Arch / M.Sc degree or currently studying in 3rd year or higher.")
        ],
        "how_to_apply": [
            "Register on the official GOAPS GATE portal with verified credentials.",
            "Fill in personal data, graduation marks, and select preferred exam cities.",
            "Upload photo, signature, valid photo ID, and degree/study certificate.",
            "Complete online application fee payment and print the application summary."
        ],
        "links": [
            ("Apply Online GOAPS", "https://gate2027.iit.ac.in/", "Click Here"),
            ("Download Information Brochure", "https://gate2027.iit.ac.in/", "Click Here"),
            ("GATE Official Website", "https://gate2027.iit.ac.in/", "Click Here")
        ],
        "faqs": [
            ("What is the validity period of GATE scorecard?", "GATE score remains valid for 3 years from the date of result announcement.")
        ]
    },
    {
        "slug": "up-deled-2026",
        "title": "UP DELEd (BTC) 2026 Online Counselling",
        "category": "admission",
        "post_date": "August 19, 2026",
        "post_time": "11:10 am",
        "short_desc": "Examination Regulatory Authority (PNP) Prayagraj, Uttar Pradesh releases state rank cards, counselling schedule, and college seat choice filling portal for Diploma in Elementary Education (D.El.Ed BTC 2026).",
        "start_date": "Counselling Start: August 2026",
        "last_date": "Choice Filling: September 2026",
        "fee_last_date": "September 2026",
        "exam_date": "State Rank Based Merit",
        "fee_gen": "₹ 5,000/- (Advance Allotment Fee)",
        "fee_res": "₹ 5,000/- (Adjusted in college fee)",
        "age_min": "18 Years",
        "age_max": "35 Years",
        "total_posts": "2,33,350 D.El.Ed Seats",
        "vacancy_rows": [
            ("UP D.El.Ed (BTC) 2-Year Diploma Course", "2,33,350 Seats (DIET + Private)", "Graduation degree with minimum 50% marks (45% for SC/ST/OBC) and state merit rank.")
        ],
        "how_to_apply": [
            "Visit the official portal at updeled.gov.in.",
            "Generate candidate OTP and log in with registration number.",
            "Lock your preferred government DIET and private college choices.",
            "Check seat allotment result and download college allocation letter.",
            "Report to the assigned DIET/college with original credentials for final admission."
        ],
        "links": [
            ("Counselling Choice Filling Portal", "https://updeled.gov.in/", "Click Here"),
            ("Check State Rank Card", "https://updeled.gov.in/", "Click Here"),
            ("UP D.El.Ed Official Website", "https://updeled.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How are seats allocated in UP D.El.Ed 2026?", "Seats are allocated based on candidate state rank calculated from 10th, 12th, and graduation marks.")
        ]
    },

    # ==================== CERTIFICATE VERIFICATION & IMPORTANT (5 Posts) ====================
    {
        "slug": "voter-id-card-online-apply-2026",
        "title": "Voter ID Card Online Application & Correction 2026",
        "category": "certificate-verification",
        "post_date": "August 19, 2026",
        "post_time": "08:00 am",
        "short_desc": "Election Commission of India (ECI) invites citizens to apply online for new Voter ID (Form 6), correction of personal details (Form 8), and download digital e-EPIC card through the National Voters' Service Portal (ECI Voters Portal).",
        "start_date": "Active 24x7",
        "last_date": "Open Throughout Year",
        "fee_last_date": "N/A",
        "exam_date": "Instant / Online Processing",
        "fee_gen": "₹ 00/- (100% Free Service)",
        "fee_res": "₹ 00/- (Free)",
        "age_min": "18 Years (or 17+ advance application)",
        "age_max": "No Upper Limit",
        "total_posts": "National Citizen Service",
        "vacancy_rows": [
            ("New Voter ID Registration (Form 6)", "All Indian Citizens", "Citizen having completed 18 years with valid address proof and photograph."),
            ("Correction in Existing Voter ID (Form 8)", "All Registered Voters", "Correction in name, age, address, photo, or relative details.")
        ],
        "how_to_apply": [
            "Visit the official ECI Voters Portal at voters.eci.gov.in.",
            "Sign up using your mobile number and authenticate via OTP.",
            "Choose Form 6 for new registration or Form 8 for correction.",
            "Upload passport size photo, age proof, and address proof document.",
            "Submit the form and track your Application Reference Number online."
        ],
        "links": [
            ("Apply Online New Voter Card (Form 6)", "https://voters.eci.gov.in/", "Click Here"),
            ("Download Digital e-EPIC Card", "https://voters.eci.gov.in/", "Click Here"),
            ("Track Application Status", "https://voters.eci.gov.in/", "Click Here"),
            ("ECI Official Website", "https://voters.eci.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the official portal for Voter ID services?", "The official portal is voters.eci.gov.in.")
        ]
    },
    {
        "slug": "pan-card-online-apply-2026",
        "title": "NSDL / UTIITSL PAN Card Online Apply & Instant e-PAN",
        "category": "certificate-verification",
        "post_date": "August 19, 2026",
        "post_time": "08:30 am",
        "short_desc": "Income Tax Department of India facilitates online application for new Permanent Account Number (PAN Form 49A), reprint of physical PVC card, and instant free e-PAN generation through Aadhaar verification.",
        "start_date": "Active 24x7",
        "last_date": "Open Year Round",
        "fee_last_date": "N/A",
        "exam_date": "7 to 10 Days Delivery",
        "fee_gen": "₹ 107/- (Physical Card) / Free (Instant e-PAN)",
        "fee_res": "Same for all applicants",
        "age_min": "No Minimum Age",
        "age_max": "No Upper Limit",
        "total_posts": "Income Tax Department Service",
        "vacancy_rows": [
            ("New PAN Card (Form 49A)", "National Taxpayer Card", "Aadhaar Card with linked mobile number for paperless OTP verification.")
        ],
        "how_to_apply": [
            "Visit the NSDL (Protean) or UTIITSL online PAN application portal.",
            "Select Application Type as New PAN - Indian Citizen (Form 49A).",
            "Fill applicant personal information and verify via Aadhaar OTP.",
            "Complete online processing fee payment and note down acknowledgment receipt."
        ],
        "links": [
            ("Apply Online NSDL Portal", "https://www.onlineservices.nsdl.com/", "Click Here"),
            ("Apply Instant e-PAN (Income Tax)", "https://www.incometax.gov.in/", "Click Here"),
            ("Income Tax Official Website", "https://www.incometax.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How long does it take to receive a physical PAN card?", "Physical PVC cards are typically delivered to the registered address within 7 to 10 working days.")
        ]
    },
    {
        "slug": "aadhar-card-update-download-2026",
        "title": "UIDAI Aadhar Card Online Update, Correction & Download",
        "category": "certificate-verification",
        "post_date": "August 19, 2026",
        "post_time": "09:00 am",
        "short_desc": "Unique Identification Authority of India (UIDAI) provides online services on the myAadhaar portal for updating address, document revalidation, checking PVC card order status, and downloading masked/regular e-Aadhaar PDF.",
        "start_date": "Active 24x7",
        "last_date": "Open Year Round",
        "fee_last_date": "N/A",
        "exam_date": "Instant Download",
        "fee_gen": "₹ 50/- for PVC Card / Free Online Download",
        "fee_res": "Same for all citizens",
        "age_min": "All Ages",
        "age_max": "No Limit",
        "total_posts": "UIDAI National Identity",
        "vacancy_rows": [
            ("myAadhaar Online Document & Address Update", "All Aadhaar Holders", "Registered mobile number linked with Aadhaar for OTP authentication.")
        ],
        "how_to_apply": [
            "Open myaadhaar.uidai.gov.in on your web or mobile browser.",
            "Log in using your 12-digit Aadhaar number and OTP received on registered mobile.",
            "Select the required service: Download Aadhaar, Order PVC Card, or Update Address.",
            "Submit valid supporting document proof and complete request submission."
        ],
        "links": [
            ("Download e-Aadhaar PDF", "https://myaadhaar.uidai.gov.in/", "Click Here"),
            ("Order Aadhaar PVC Card", "https://myaadhaar.uidai.gov.in/", "Click Here"),
            ("UIDAI Official Website", "https://uidai.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the default password to open downloaded e-Aadhaar PDF?", "The password is the first 4 letters of your name in CAPITAL followed by your birth year (e.g. AMAN1998).")
        ]
    },
    {
        "slug": "bihar-rtps-caste-income-residential-certificate",
        "title": "Bihar RTPS Service Online Caste, Income & Residence Certificate",
        "category": "certificate-verification",
        "post_date": "August 19, 2026",
        "post_time": "09:30 am",
        "short_desc": "Government of Bihar provides online issuance and electronic verification of Jati (Caste), Aay (Income), Niwas (Residential), Non-Creamy Layer (NCL), and EWS certificates through the ServicePlus RTPS portal.",
        "start_date": "Active 24x7",
        "last_date": "Open Year Round",
        "fee_last_date": "N/A",
        "exam_date": "Issued in 10-14 Days",
        "fee_gen": "₹ 00/- (Free Government Service)",
        "fee_res": "₹ 00/- (Free)",
        "age_min": "Bihar Resident",
        "age_max": "No Limit",
        "total_posts": "Bihar e-Governance Services",
        "vacancy_rows": [
            ("Caste, Income & Domicile Certificates", "All Citizens of Bihar", "Permanent resident of Bihar with Aadhaar and family declaration.")
        ],
        "how_to_apply": [
            "Visit serviceonline.bihar.gov.in.",
            "Choose General Administration Department in the service catalogue.",
            "Select required certificate level (CO / SDO / DM).",
            "Fill applicant credentials, upload photo, and submit application.",
            "Download digitally signed certificate using Application Reference Number."
        ],
        "links": [
            ("Apply Online on Bihar RTPS", "https://serviceonline.bihar.gov.in/", "Click Here"),
            ("Download Issued Certificate", "https://serviceonline.bihar.gov.in/", "Click Here"),
            ("Bihar RTPS Official Website", "https://serviceonline.bihar.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Where can I download my Bihar caste or income certificate?", "Directly from the ServicePlus RTPS portal at serviceonline.bihar.gov.in.")
        ]
    },
    {
        "slug": "up-edistrict-certificate-verification",
        "title": "UP eDistrict Caste, Income, Domicile & Birth Certificate Verification",
        "category": "certificate-verification",
        "post_date": "August 19, 2026",
        "post_time": "10:00 am",
        "short_desc": "Revenue Department, Government of Uttar Pradesh enables citizens to apply for and verify Jati Praman Patra, Aay Praman Patra, Niwas Praman Patra, and Divyang certificates online via the UP eDistrict citizen portal.",
        "start_date": "Active 24x7",
        "last_date": "Open Year Round",
        "fee_last_date": "N/A",
        "exam_date": "Processed in 7-15 Days",
        "fee_gen": "₹ 15/- (Citizen Portal Service Charge)",
        "fee_res": "₹ 15/-",
        "age_min": "Resident of UP",
        "age_max": "No Limit",
        "total_posts": "UP Revenue Department Services",
        "vacancy_rows": [
            ("UP Revenue Praman Patra Issuance & Verification", "All UP Residents", "Valid proof of residence, ration card/Aadhaar and self-declaration affidavit.")
        ],
        "how_to_apply": [
            "Visit edistrict.up.gov.in and click on Citizen Login (eSathi).",
            "Register or log in to your account.",
            "Select the certificate type from the application menu.",
            "Upload self-declaration form and applicant photo.",
            "Pay the nominal fee and track certificate verification status."
        ],
        "links": [
            ("Citizen Login (eSathi UP)", "https://esathi.up.gov.in/", "Click Here"),
            ("Certificate Verification Search", "https://edistrict.up.gov.in/", "Click Here"),
            ("UP eDistrict Official Website", "https://edistrict.up.gov.in/", "Click Here")
        ],
        "faqs": [
            ("How can I verify a UP caste or income certificate?", "Enter the Application Number and Certificate Number in the verification box on edistrict.up.gov.in.")
        ]
    }
]

print(f"Total universal posts to generate: {len(posts_data)}")

custom_posts_list = []
all_posts_list = []

def generate_post_page(p):
    soup = BeautifulSoup(MASTER_BLUEPRINT, 'html.parser')

    title = p["title"]
    slug = p["slug"]
    category = p["category"]

    # 1. Page Title & Head Tags
    if soup.title:
        soup.title.string = f"{title} | STUDY TOPPER™"

    # 2. H1
    h1 = soup.find('h1')
    if h1:
        h1.string = title

    # 3. Subheadings
    h2 = soup.find('h2')
    if h2:
        h2.string = f"{title} – Latest Details & Updates"

    h3 = soup.find('h3')
    if h3:
        h3.string = f"{title} : Short Details"

    # 4. Post Date & Time
    time_tag = soup.find('time', class_='entry-date')
    if time_tag:
        time_tag.string = p["post_date"]
    
    post_time_span = soup.find(class_='custom-post-time')
    if post_time_span:
        post_time_span.string = p["post_time"]

    # 5. Short Details Paragraph
    short_details_p = soup.find(class_='short_Details')
    if short_details_p:
        inner_p = short_details_p.find('p')
        if inner_p:
            inner_p.string = p["short_desc"]
        else:
            short_details_p.string = p["short_desc"]

    # 6. Important Dates Box
    dates_box = soup.find(class_='gb-container-16a90584')
    if dates_box:
        ul = dates_box.find('ul')
        if ul:
            ul.clear()
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Start Date : <strong>{p["start_date"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Last Date : <span style="color: #ff0000;"><strong>{p["last_date"]}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Last Date For Fee Payment : <span style="color: #000000;"><strong>{p["fee_last_date"]}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 18.6667px;">Exam / Merit Date : <strong>{p["exam_date"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Candidates are advised to confirm from the official website.</span></li>', 'html.parser'))

    # 7. Application Fee Box
    fee_box = soup.find(class_='gb-container-fcbb81ff')
    if fee_box:
        uls = fee_box.find_all('ul')
        if uls:
            uls[0].clear()
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>General/ OBC/ EWS</strong> : <strong>{p["fee_gen"]}</strong></span></li>', 'html.parser'))
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>SC/ ST/ PH / Female</strong> : <strong>{p["fee_res"]}</strong></span></li>', 'html.parser'))

    # 8. Age Limit Box
    age_box = soup.find(class_='gb-container-0f18d865')
    if age_box:
        ul = age_box.find('ul')
        if ul:
            ul.clear()
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Minimum Age : <strong>{p["age_min"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Maximum Age : <strong>{p["age_max"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Age relaxation provided for reserved categories as per official regulations.</span></li>', 'html.parser'))

    # 9. Total Post Count Badge
    total_post_badge = soup.find(class_='gb-headline-4259c0c2')
    if total_post_badge:
        total_post_badge.string = p["total_posts"]

    # 10. Vacancy Details & Eligibility Table
    tables = soup.find_all('table')
    if len(tables) >= 2:
        # Table 2 is typically the vacancy/eligibility table in post_design_preview
        elig_tbl = tables[1]
        elig_tbl.clear()
        
        # Header row
        tr_head = soup.new_tag('tr')
        th1 = soup.new_tag('th')
        th1.string = "Post Name"
        th2 = soup.new_tag('th')
        th2.string = "Total Posts"
        th3 = soup.new_tag('th')
        th3.string = "Eligibility Criteria"
        tr_head.append(th1)
        tr_head.append(th2)
        tr_head.append(th3)
        elig_tbl.append(tr_head)

        for name, count, reqs in p["vacancy_rows"]:
            tr = soup.new_tag('tr')
            td1 = soup.new_tag('td')
            td1.string = name
            td2 = soup.new_tag('td')
            td2.string = count
            td3 = soup.new_tag('td')
            td3.string = reqs
            tr.append(td1)
            tr.append(td2)
            tr.append(td3)
            elig_tbl.append(tr)

    # 11. How to Apply Table
    if len(tables) >= 4:
        how_tbl = tables[3]
        tbody = how_tbl.find('tbody') or how_tbl
        rows = tbody.find_all('tr')
        if len(rows) >= 2:
            step_td = rows[1].find('td')
            if step_td:
                ol_steps = "".join([f"<li style='margin-bottom:6px;'>{s}</li>" for s in p["how_to_apply"]])
                step_td.clear()
                step_td.append(BeautifulSoup(f"<ol style='margin:0; padding-left:18px;'>{ol_steps}</ol>", 'html.parser'))

    # 12. Useful Links Table
    if len(tables) >= 7:
        links_tbl = tables[6]
        links_tbl.clear()
        for lname, lurl, laction in p["links"]:
            color = "#00a82d" if "whatsapp" in lname.lower() else ("#0088cc" if "telegram" in lname.lower() else "#0000ef")
            tr = soup.new_tag('tr')
            td1 = soup.new_tag('td')
            td1.append(BeautifulSoup(f"<h5 style='margin:4px 0; font-weight:bold;'>{lname}</h5>", 'html.parser'))
            td2 = soup.new_tag('td')
            td2.append(BeautifulSoup(f"<h5 style='margin:4px 0;'><a href='{lurl}' target='_blank' rel='noopener noreferrer' style='color:{color}; font-weight:bold; text-decoration:underline;'>{laction}</a></h5>", 'html.parser'))
            tr.append(td1)
            tr.append(td2)
            links_tbl.append(tr)

    # 13. FAQs Table
    if len(tables) >= 8:
        faq_tbl = tables[7]
        faq_tbl.clear()
        tr_head = soup.new_tag('tr')
        td_head = soup.new_tag('td', colspan="2")
        td_head.append(BeautifulSoup(f"<strong style='font-size:15px; color:#0b213f;'>{title} : Frequently Asked Questions (FAQ)</strong>", 'html.parser'))
        tr_head.append(td_head)
        faq_tbl.append(tr_head)

        for q, a in p["faqs"]:
            tr_q = soup.new_tag('tr')
            td_q = soup.new_tag('td', colspan="2")
            td_q.append(BeautifulSoup(f"<strong>Q. {q}</strong><br><span style='color:#333333;'>Ans: {a}</span>", 'html.parser'))
            tr_q.append(td_q)
            faq_tbl.append(tr_q)

    # Write generated standalone HTML page to pages/{slug}.html
    out_file = os.path.join(PAGES_DIR, f"{slug}.html")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f" [OK] Generated Universal Post: pages/{slug}.html")

    # Record post metadata
    post_record = {
        "id": f"post_{slug.replace('-', '_')}",
        "slug": slug,
        "title": title,
        "category": category,
        "short_desc": p["short_desc"],
        "application_start_date": p["start_date"],
        "application_last_date": p["last_date"],
        "custom_badge": "",
        "tags": f"{category}, Govt Job, Study Topper",
        "created_at": datetime.datetime.now().isoformat()
    }
    custom_posts_list.append(post_record)
    all_posts_list.append(post_record)

for p in posts_data:
    generate_post_page(p)

# 4. Save metadata to custom_posts.json and all_posts.json
with open(os.path.join(DATA_DIR, 'custom_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(custom_posts_list, f, indent=2)

with open(os.path.join(DATA_DIR, 'all_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(all_posts_list, f, indent=2)

# 5. Save category data to category_data.json
cat_data = {}
for p in custom_posts_list:
    cat = p.get('category', 'latest-jobs')
    if cat not in cat_data:
        cat_data[cat] = []
    cat_data[cat].append({
        'title': p.get('title'),
        'url': f"/{p.get('slug')}/",
        'short_desc': p.get('short_desc', ''),
        'date': p.get('application_start_date', '')
    })

with open(os.path.join(DATA_DIR, 'category_data.json'), 'w', encoding='utf-8') as f:
    json.dump(cat_data, f, indent=2)

# 6. Update Homepage category lists (pages/index.html & original_index.html)
category_column_map = {
    'gb-grid-column-0b76599a': 'result',
    'gb-grid-column-c7488d9a': 'latest-jobs',
    'gb-grid-column-e64d3148': 'admit-card',
    'gb-grid-column-d19ddc59': 'answer-key',
    'gb-grid-column-b48dca36': 'syllabus',
    'gb-grid-column-51daea0e': 'admission'
}

def sync_index_file(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    for col_cls, cat_key in category_column_map.items():
        col = soup.find(class_=col_cls)
        if col:
            ul = col.find('ul')
            if ul:
                ul.clear()
                cat_posts = cat_data.get(cat_key, [])
                for item in cat_posts[:5]:
                    li = soup.new_tag('li')
                    a = soup.new_tag('a', href=item['url'], class_='wp-block-latest-posts__post-title')
                    a.string = item['title']
                    li.append(a)
                    ul.append(li)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f" [OK] Synced category columns in {filepath}")

sync_index_file(os.path.join(PAGES_DIR, 'index.html'))
sync_index_file(os.path.join(BASE_DIR, 'original_index.html'))

print("\nRebuild complete! All posts on website are now 100% in Universal Design Layout with 5 posts per category.")
