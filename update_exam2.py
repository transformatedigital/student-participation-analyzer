#!/usr/bin/env python3
"""
Script to update Exam 2 data in the dashboard.html file
"""

import json
import re

# Read the dashboard file
with open('docs/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new Exam 2 data
exam2_data = {
    "id": 2,
    "date": "2026-05-19",
    "date_label": "Tue, May 19 (Wk 12)",
    "title": "Exam 2 — Problem-Demand Fit Definition",
    "n_sections": 6,
    "sections": [
        {
            "id": "S1",
            "name": "Initiative Overview",
            "max_score": 20,
            "subsections": ["Course Objective", "Real Problem", "Ownership", "Expected Impact"]
        },
        {
            "id": "S2",
            "name": "Root Cause (3 Whys)",
            "max_score": 20,
            "subsections": ["Why 1", "Why 2", "Why 3", "Final Root Cause"]
        },
        {
            "id": "S3",
            "name": "Conceptual Framework",
            "max_score": 20,
            "subsections": ["Problem", "Symptom", "Solution", "Technology", "Component/Platform"]
        },
        {
            "id": "S4",
            "name": "Gap Identification",
            "max_score": 10,
            "subsections": ["Gap(s) Identified"]
        },
        {
            "id": "S5",
            "name": "Quality Check",
            "max_score": 15,
            "subsections": ["Specificity", "Owner", "Evidence", "Check-up Test"]
        },
        {
            "id": "S6",
            "name": "Final Statement",
            "max_score": 15,
            "subsections": ["Context", "Group", "Problem", "Root Cause", "Impact"]
        }
    ],
    "responses": {
        "Aryang": {
            "full_name": "ARYA C.G.S",
            "s1_responses": [
                "The primary course of GTC is to commercialize the technology from the lab to the market to increase the value of ideas from the lab so it can be more valuable. Also to teach us to become the next global leader, but instead just doing theoretical things, we also combine into practical things, like build the ICP, so we can act as an intermediary between the source (our country) and recipient (Korea).",
                "Bank Rakyat Indonesia (BRI) as the biggest bank in Indonesia wants to provide personalized solution for its customers. BRI wants to upgrade its text chatbot to voice chatbot solutions. BUT, nowadays no voice AI solution provides both regulatory compliance and high accuracy for Indonesian language model.",
                "Enterprise Data Division (EDM). This initiative also stated in their division target (Jan 2026).",
                "Success to co-develop the TTS model for Indonesian language. Korea partner increases its capability for Indonesian voice. BRI can combine its model to their chatbot."
            ],
            "s2_responses": [
                "BRI wants to make personalized solution.",
                "Personalized in BRI means voice — from text chatbot to voice chatbot.",
                "Voice AI developed by our own? NO EXPERTISE. Partnership with vendor? NO Indonesian Data Center, if any, NO HIGH ACCURACY.",
                "No TTS model that complies with Indonesia regulatory & high accuracy."
            ],
            "s3_responses": [
                "To create personalized solution, BRI wants to upgrade from text chatbot to voice chatbot.",
                "Develop by BRI? No expertise. Partnership? No solution that complies with Indonesia regulation & high accuracy.",
                "Develop with the support partner — TTS model.",
                "TTS model.",
                "Voice AI."
            ],
            "s4_responses": [
                "[O] Other: I am pursuing this because of my organization initiative."
            ],
            "s5_responses": [
                "YES — it's BRI problem and narrow down to EDM target.",
                "YES — the EDM division.",
                "1. BRI pub ex, 2. IT Directorate role 5-year plan, 3. EDM division target.",
                "✅ YES"
            ],
            "s6_responses": [
                "BRI wants to make personalized solution.",
                "EDM division needs to upgrade their chatbot.",
                "From text chatbot to voice chatbot.",
                "No TTS model that complies for regulation & high accuracy.",
                "BRI/EDM cannot deliver the personalized voice chatbot for customers."
            ],
            "scores": [None, None, None, None, None, None]
        },
        "Chilaka": {
            "full_name": "CHILAKA CHIJIOKE REGINALD",
            "s1_responses": [
                "The aim and objective of the GTC is to be a bridge from our country and Korea and solve a real problem of our country that will create value to the people in our country. To also better understand our roles as intermediaries in the process of creating value for our country.",
                "It aims to address the fragmentation of R&D data across multiple ministries, departments, agencies and institutions. This has led to multiple duplication of budget to finance same R&D projects scattered across different institutions. In summary, it is trying to solve the silo issue prevalent in developing economies.",
                "Federal Ministry of Innovation, Science and Technology (supervising). National Board for Technology Incubation (NBTI) will host the project.",
                "It will save the country budget wastages on duplicate projects. Will lead to more commercializable products as R&D will be unified instead of in silos, which will translate to more local production and help the economy."
            ],
            "s2_responses": [
                "Research outputs do not get to the market for commercialization — duplication of R&D data and output across different MDAs.",
                "The research data and output are scattered across different MDAs in the country.",
                "Nigeria does not have a general/central governance framework.",
                "A unified one-stop platform for all R&D activities."
            ],
            "s3_responses": [
                "The real problem that stays even when the technology disappears.",
                "The issues that are raised as a result of the problems.",
                "A proven system that will solve the problem.",
                "A P (incomplete/illegible)",
                "(No response)"
            ],
            "s4_responses": [
                "[ ] Other: Still sieving it through. (No box checked)"
            ],
            "s5_responses": [
                "I believe so.",
                "Yes.",
                "Specific country data and policies.",
                "✅ YES"
            ],
            "s6_responses": [
                "(No response)",
                "Nigeria",
                "Duplication of budget allocation and low commercialization.",
                "Duplication of R&D data across multiple MDAs.",
                "Shortage of limited funds and low commercialization."
            ],
            "scores": [None, None, None, None, None, None]
        },
        "Grace": {
            "full_name": "SONGANZILA MFUMU GRACE",
            "s1_responses": [
                "This course has goal to help students to understand how the technology is made from the lab to the market. As for GDI, this course is very important to help students to build a strong partnership between Korea and their home countries through the technology knowledge transfer from Korean company to solve an identified problem.",
                "My GTC initiative aims to solve a longstanding academic management problem within the University of Kinshasa. The University of Kinshasa lacks an efficient academic management system from student identification, registration, faculty management, and administrative management due to less integration of digital technology. Many tasks are done manually, resulting in delays, errors, underperformance from students to professors as well as slow administration.",
                "The University of Kinshasa.",
                "If successful, this GTC initiative would improve the academic management system by integrating a smart academic management system covering learning process, academic documents records and control, student management and registration, and overall academic and administrative tasks."
            ],
            "s2_responses": [
                "Lack of efficient academic management system.",
                "Skills gap.",
                "Financial issues.",
                "(No response)"
            ],
            "s3_responses": [
                "The University of Kinshasa faces a longstanding academic management system problem within its organization — student registration, learning process, documents issuance, record and verification, and communication.",
                "(No response)",
                "Deployment of smart academic management system for efficient academic and administrative management within the University of Kinshasa.",
                "Cloud-based technology, web-based, suitable with mobile.",
                "Student registration and management. Learning process (course slots and management). Document issuance, records, control and verification. Inter-communication among faculties. Online learning. Online library."
            ],
            "s4_responses": [
                "(No option checked — all blank)"
            ],
            "s5_responses": [
                "(No response)",
                "(No response)",
                "(No response)",
                "(No response)"
            ],
            "s6_responses": [
                "(No response)",
                "(No response)",
                "(No response)",
                "(No response)",
                "(No response)"
            ],
            "scores": [None, None, None, None, None, None]
        },
        "Mega": {
            "full_name": "MEGAWATI SUNARSONO PUTRI",
            "s1_responses": [
                "Make a collaboration between Korea as a developed country to our country (developing country). To build an innovation, we cannot do it alone. We need a collaboration. For Korea, the technology is not only stopped in invention but it also can be innovation.",
                "Indonesia is a large country — outside Java Island there is no electricity. The electricity source in Java is from coal (coal power plant) which destroys mining areas and creates bad environmental and health impacts. Some areas/islands have no electricity. Government (President Vision) mandates a National Program for PV in every province (2026). The problem in photovoltaic (PV) is it cannot produce electricity during night or bad weather (rain).",
                "National Research and Innovation Agency (BRIN).",
                "Indonesia can use proven technology from Korea. Korea can promote its technology in Indonesia — this program is currently a big National Program and the President is very concerned about this."
            ],
            "s2_responses": [
                "Poverty.",
                "There is no economy activities.",
                "There is no electricity.",
                "No electricity."
            ],
            "s3_responses": [
                "There is no electricity (outside Java Island). Pollution / Healthiness.",
                "Low economic activity. A lot of cancer in mining area and near CPP.",
                "Electricity from New and Renewable Energy.",
                "PV + BESS.",
                "(No response)"
            ],
            "s4_responses": [
                "✅ Solution Bias. ✅ Lack of Focus."
            ],
            "s5_responses": [
                "Yes.",
                "Yes.",
                "Healthiness impact, carbon emission, economic, President Vision.",
                "✅ YES"
            ],
            "s6_responses": [
                "Indonesia.",
                "Java Island.",
                "Pollution and healthiness problem.",
                "Carbon emission.",
                "Coal power plant impact. Indonesia outside Java Island faces poverty because there is no electricity/economic activity/regulation."
            ],
            "scores": [None, None, None, None, None, None]
        },
        "Sthepen": {
            "full_name": "GAKUNBA STEPHENS",
            "s1_responses": [
                "① To know how to make the ICP more realistic to our country like understanding the real problem. GTC means how to make the idea from the lab to the market to add value (money). ② To know if our ICP is problem driven or solution push. ③ To understand clearly the problem scope, all the stakeholders involved and how to make collaboration between two countries (Rwanda and Korea).",
                "① I am trying to protect the citizen not losing their money on their phone. ② Protecting the use of ID in ecosystems. More citizens have started to fear to use momo (mobile money in payments). ③ The vision of my country is to become a cashless country but now we have issues in e-payment like scamming on phones for those who use mobile money in transactions.",
                "RURA (Rwanda Utility Regulation Agency). NIDA (National Identification Agency).",
                "① People are not losing their money through scamming on phones. ② Restoring trust to the people who use momo (mobile money) to send, transfer and pay by using their phone. ③ Citizens will have trust in e-payment in Rwanda."
            ],
            "s2_responses": [
                "Real gap for monitoring.",
                "No regulation to tell the MNO to do it.",
                "Currently no any tool that MNO has to prevent scamming.",
                "The current regulation mandates the MNO to register SIM by the use of ID number through biometric authentication, but after registration we don't know what that SIM card is being used for."
            ],
            "s3_responses": [
                "\"Real time gap.\"",
                "Mobile users are losing their money through scamming.",
                "AI detection for smishing and vishing (SMS and voice) on MNO's network level.",
                "AI that is using NLP.",
                "Voice and SMS (Vishing/Smishing)."
            ],
            "s4_responses": [
                "✅ Technology-First. ✅ Lack of Focus."
            ],
            "s5_responses": [
                "Yes — more now I understand my ICP.",
                "Yes.",
                "Several meetings we had as a country and email.",
                "✅ YES"
            ],
            "s6_responses": [
                "Rwanda is aiming to become a cashless country.",
                "Mobile money users.",
                "Mobile money users are losing their money.",
                "The absence of real time monitoring.",
                "Money users forced to pay using mobile money (text cut off at margin)."
            ],
            "scores": [None, None, None, None, None, None]
        }
    },
    "status": "grading"
}

# Convert to JSON string (compact format for insertion)
exam2_json = json.dumps(exam2_data, ensure_ascii=False, separators=(',', ': '))

# Find and replace the old Exam 2 entry
old_exam2_pattern = r'\{"id": 2, "date": "2026-05-19", "date_label": "Tue, May 19 \(Wk 12\)", "title": "Exam 2 — Pending", "status": "pending"\}'

# Replace the old exam 2 data with the new data
content = re.sub(old_exam2_pattern, exam2_json, content)

# Write back to file
with open('docs/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Exam 2 data updated successfully in docs/dashboard.html")
print("📊 Exam 2: Problem-Demand Fit Definition")
print("   - 6 sections with varying scores (S1-20, S2-20, S3-20, S4-10, S5-15, S6-15)")
print("   - 5 students: Aryang, Chilaka, Grace, Mega, Sthepen")
print("   - Status: grading (ready for professor to add scores)")
print("\n⚠️  Note: All scores are set to null - professor needs to fill them in")
