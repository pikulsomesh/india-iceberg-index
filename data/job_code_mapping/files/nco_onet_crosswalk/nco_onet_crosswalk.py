#!/usr/bin/env python3
"""
NCO-O*NET Occupation Crosswalk Generator

This script creates a crosswalk mapping between India's National Classification 
of Occupations (NCO) 2015/2004 and the US Bureau of Labor Statistics O*NET 
occupation classification system.

The mapping uses a semantic approach that:
1. Matches occupation titles using domain-specific keywords
2. Uses the NCO hierarchical code structure (first 4 digits = occupational family)
3. Falls back to division-level defaults when specific matches aren't found

This preserves semantic meaning rather than relying on simple text similarity,
which can produce incorrect mappings (e.g., mycologist → dentist instead of biologist).

Author: Generated for occupational research
License: MIT
Version: 1.0.0

Requirements:
    - pdfplumber
    - rapidfuzz

Usage:
    python nco_onet_crosswalk.py --nco <path_to_nco_pdf> --onet <path_to_onet_pdf> --output <output_csv>

Input Files:
    - NCO 2015 PDF: "national_classification_of_occupations__vol_i-_2015.pdf"
      Contains concordance table with NCO 2015, NCO 2004 codes and job titles
    - O*NET PDF: List of O*NET-SOC occupation codes and titles
      Available from https://www.onetonline.org/

Output:
    CSV file with columns:
    - NCO_2015_Code: India's 2015 classification code (format: XXXX.XXXX)
    - NCO_2004_Code: Corresponding 2004 code if available (format: XXXX.XX)
    - NCO_Job_Title: Occupation title from NCO
    - ONET_Code: Matched US O*NET code (format: XX-XXXX.XX)
    - ONET_Job_Title: Occupation title from O*NET
    - Match_Score: Confidence score (0-100)
        - 95: Semantic keyword match
        - 80: NCO prefix (4-digit) match
        - 75: NCO prefix (3-digit) match  
        - 60: Division-level fallback
"""

import pdfplumber
import re
import csv
import argparse
import os
from typing import Dict, List, Tuple, Optional


# =============================================================================
# SEMANTIC KEYWORD MAPPINGS
# =============================================================================
# These map specific occupation keywords to appropriate O*NET codes.
# Keywords are matched in order of length (longest first) to ensure
# more specific terms take precedence.

SEMANTIC_KEYWORDS: Dict[str, Tuple[str, str]] = {
    # -------------------------------------------------------------------------
    # Legal Professions
    # -------------------------------------------------------------------------
    'judge': ('23-1023.00', 'Judges, Magistrate Judges, and Magistrates'),
    'justice': ('23-1023.00', 'Judges, Magistrate Judges, and Magistrates'),
    'magistrate': ('23-1023.00', 'Judges, Magistrate Judges, and Magistrates'),
    'tribunal': ('23-1023.00', 'Judges, Magistrate Judges, and Magistrates'),
    'lawyer': ('23-1011.00', 'Lawyers'),
    'advocate': ('23-1011.00', 'Lawyers'),
    'attorney': ('23-1011.00', 'Lawyers'),
    'solicitor': ('23-1011.00', 'Lawyers'),
    'barrister': ('23-1011.00', 'Lawyers'),
    'paralegal': ('23-2011.00', 'Paralegals and Legal Assistants'),
    
    # -------------------------------------------------------------------------
    # Government/Administrative Officials
    # -------------------------------------------------------------------------
    'elected official': ('11-1031.00', 'Legislators'),
    'legislator': ('11-1031.00', 'Legislators'),
    'diplomat': ('11-1011.00', 'Chief Executives'),
    'administrative official': ('11-1011.00', 'Chief Executives'),
    'executive official': ('11-1011.00', 'Chief Executives'),
    'government official': ('11-1011.00', 'Chief Executives'),
    'chief executive': ('11-1011.00', 'Chief Executives'),
    'chairman': ('11-1011.00', 'Chief Executives'),
    'registrar': ('11-9033.00', 'Education Administrators, Postsecondary'),
    'treasurer': ('11-3031.00', 'Financial Managers'),
    'controller': ('11-3031.00', 'Financial Managers'),
    
    # -------------------------------------------------------------------------
    # Education - Higher Education
    # -------------------------------------------------------------------------
    'professor': ('25-1099.00', 'Postsecondary Teachers, All Other'),
    'lecturer': ('25-1099.00', 'Postsecondary Teachers, All Other'),
    'university': ('25-1099.00', 'Postsecondary Teachers, All Other'),
    'college teacher': ('25-1099.00', 'Postsecondary Teachers, All Other'),
    'principal, college': ('11-9033.00', 'Education Administrators, Postsecondary'),
    'principal': ('11-9032.00', 'Education Administrators, Kindergarten through Secondary'),
    'headmaster': ('11-9032.00', 'Education Administrators, Kindergarten through Secondary'),
    'school inspector': ('11-9032.00', 'Education Administrators, Kindergarten through Secondary'),
    'education officer': ('11-9032.00', 'Education Administrators, Kindergarten through Secondary'),
    
    # -------------------------------------------------------------------------
    # Medical/Health Professionals
    # -------------------------------------------------------------------------
    'physician': ('29-1216.00', 'General Internal Medicine Physicians'),
    'doctor': ('29-1216.00', 'General Internal Medicine Physicians'),
    'surgeon': ('29-1248.00', 'Surgeons, All Other'),
    'nursing': ('29-1141.00', 'Registered Nurses'),
    'nurse,': ('29-1141.00', 'Registered Nurses'),
    'nurses': ('29-1141.00', 'Registered Nurses'),
    'dentist': ('29-1021.00', 'Dentists, General'),
    'pharmacist': ('29-1051.00', 'Pharmacists'),
    'veterinarian': ('29-1131.00', 'Veterinarians'),
    'optometrist': ('29-1041.00', 'Optometrists'),
    'physiotherapist': ('29-1123.00', 'Physical Therapists'),
    'therapist': ('29-1125.00', 'Recreational Therapists'),
    'paramedic': ('29-2043.00', 'Paramedics'),
    'midwife': ('29-9099.01', 'Midwives'),
    'ayurveda': ('29-1291.00', 'Acupuncturists'),
    'homeopath': ('29-1291.00', 'Acupuncturists'),
    'unani': ('29-1291.00', 'Acupuncturists'),
    
    # -------------------------------------------------------------------------
    # Biological Sciences
    # -------------------------------------------------------------------------
    'biologist': ('19-1029.04', 'Biologists'),
    'botanist': ('19-1029.04', 'Biologists'),
    'zoologist': ('19-1023.00', 'Zoologists and Wildlife Biologists'),
    'mycologist': ('19-1029.04', 'Biologists'),
    'algologist': ('19-1029.04', 'Biologists'),
    'microbiologist': ('19-1022.00', 'Microbiologists'),
    'geneticist': ('19-1029.03', 'Geneticists'),
    'ecologist': ('19-2041.03', 'Industrial Ecologists'),
    'silviculturist': ('19-1029.04', 'Biologists'),
    'pisciculturist': ('19-1029.04', 'Biologists'),
    'entomologist': ('19-1029.04', 'Biologists'),
    'ornithologist': ('19-1023.00', 'Zoologists and Wildlife Biologists'),
    'sericulturist': ('19-1029.04', 'Biologists'),
    'horticulturist': ('19-1013.00', 'Soil and Plant Scientists'),
    'agronomist': ('19-1013.00', 'Soil and Plant Scientists'),
    
    # -------------------------------------------------------------------------
    # Physical Sciences
    # -------------------------------------------------------------------------
    'physicist': ('19-2012.00', 'Physicists'),
    'astronomer': ('19-2011.00', 'Astronomers'),
    'chemist': ('19-2031.00', 'Chemists'),
    'geologist': ('19-2042.00', 'Geoscientists, Except Hydrologists and Geographers'),
    'hydrologist': ('19-2043.00', 'Hydrologists'),
    'hydrographer': ('19-2042.00', 'Geoscientists, Except Hydrologists and Geographers'),
    'meteorologist': ('19-2021.00', 'Atmospheric and Space Scientists'),
    'oceanographer': ('19-2042.00', 'Geoscientists, Except Hydrologists and Geographers'),
    'seismologist': ('19-2042.00', 'Geoscientists, Except Hydrologists and Geographers'),
    'mathematician': ('15-2021.00', 'Mathematicians'),
    'statistician': ('15-2041.00', 'Statisticians'),
    'actuary': ('15-2011.00', 'Actuaries'),
    
    # -------------------------------------------------------------------------
    # Social Sciences
    # -------------------------------------------------------------------------
    'economist': ('19-3011.00', 'Economists'),
    'sociologist': ('19-3041.00', 'Sociologists'),
    'psychologist': ('19-3031.00', 'Psychologists, All Other'),
    'anthropologist': ('19-3091.00', 'Anthropologists and Archeologists'),
    'archaeologist': ('19-3091.00', 'Anthropologists and Archeologists'),
    'historian': ('19-3093.00', 'Historians'),
    'geographer': ('19-3092.00', 'Geographers'),
    'political scientist': ('19-3094.00', 'Political Scientists'),
    
    # -------------------------------------------------------------------------
    # Engineering
    # -------------------------------------------------------------------------
    'engineer': ('17-2199.00', 'Engineers, All Other'),
    'civil engineer': ('17-2051.00', 'Civil Engineers'),
    'mechanical engineer': ('17-2141.00', 'Mechanical Engineers'),
    'electrical engineer': ('17-2071.00', 'Electrical Engineers'),
    'chemical engineer': ('17-2041.00', 'Chemical Engineers'),
    'architect': ('17-1011.00', 'Architects, Except Landscape and Naval'),
    'surveyor': ('17-1022.00', 'Surveyors'),
    
    # -------------------------------------------------------------------------
    # Technologists (domain-specific)
    # -------------------------------------------------------------------------
    'textile technologist': ('17-2199.00', 'Engineers, All Other'),
    'sugar technologist': ('19-1012.00', 'Food Scientists and Technologists'),
    'food technologist': ('19-1012.00', 'Food Scientists and Technologists'),
    'dairy technologist': ('19-1012.00', 'Food Scientists and Technologists'),
    'leather technologist': ('17-2199.00', 'Engineers, All Other'),
    
    # -------------------------------------------------------------------------
    # Agriculture/Farming
    # -------------------------------------------------------------------------
    'farmer': ('11-9013.00', 'Farmers, Ranchers, and Other Agricultural Managers'),
    'cultivator': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'grower': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'planter': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'rubber nursery': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'rubber plantation': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'rubber tapper': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'nursery worker': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'nursery manager': ('11-9013.00', 'Farmers, Ranchers, and Other Agricultural Managers'),
    'plantation manager': ('11-9013.00', 'Farmers, Ranchers, and Other Agricultural Managers'),
    'gardener': ('37-3011.00', 'Landscaping and Groundskeeping Workers'),
    'horticulture': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    'forester': ('19-1032.00', 'Foresters'),
    'forest ranger': ('19-1032.00', 'Foresters'),
    
    # -------------------------------------------------------------------------
    # Transportation
    # -------------------------------------------------------------------------
    'pilot': ('53-2011.00', 'Airline Pilots, Copilots, and Flight Engineers'),
    'captain': ('53-5021.00', 'Captains, Mates, and Pilots of Water Vessels'),
    'driver': ('53-3032.00', 'Heavy and Tractor-Trailer Truck Drivers'),
    'station master': ('11-1021.00', 'General and Operations Managers'),
    'train': ('53-4011.00', 'Locomotive Engineers'),
    
    # -------------------------------------------------------------------------
    # Arts/Culture/Conservation
    # -------------------------------------------------------------------------
    'restorer': ('25-4013.00', 'Museum Technicians and Conservators'),
    'conservator': ('25-4013.00', 'Museum Technicians and Conservators'),
    'curator': ('25-4012.00', 'Curators'),
    'librarian': ('25-4022.00', 'Librarians and Media Collections Specialists'),
    'archivist': ('25-4011.00', 'Archivists'),
    'musician': ('27-2042.00', 'Musicians and Singers'),
    'singer': ('27-2042.00', 'Musicians and Singers'),
    'actor': ('27-2011.00', 'Actors'),
    'dancer': ('27-2031.00', 'Dancers'),
    'choreographer': ('27-2032.00', 'Choreographers'),
    'artist': ('27-1013.00', 'Fine Artists, Including Painters, Sculptors, and Illustrators'),
    'painter': ('27-1013.00', 'Fine Artists, Including Painters, Sculptors, and Illustrators'),
    'sculptor': ('27-1013.00', 'Fine Artists, Including Painters, Sculptors, and Illustrators'),
    'photographer': ('27-4021.00', 'Photographers'),
    'journalist': ('27-3023.00', 'News Analysts, Reporters, and Journalists'),
    'reporter': ('27-3023.00', 'News Analysts, Reporters, and Journalists'),
    'editor': ('27-3041.00', 'Editors'),
    'writer': ('27-3043.00', 'Writers and Authors'),
    'author': ('27-3043.00', 'Writers and Authors'),
    
    # -------------------------------------------------------------------------
    # Musical Instruments
    # -------------------------------------------------------------------------
    'instrument maker': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'instrument tuner': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'organ tuner': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'piano tuner': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'tabla maker': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'sitar maker': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    'harmonium': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    
    # -------------------------------------------------------------------------
    # Crafts/Manufacturing
    # -------------------------------------------------------------------------
    'welder': ('51-4121.00', 'Welders, Cutters, Solderers, and Brazers'),
    'blacksmith': ('51-4199.00', 'Metal Workers and Plastic Workers, All Other'),
    'goldsmith': ('51-9071.00', 'Jewelers and Precious Stone and Metal Workers'),
    'silversmith': ('51-9071.00', 'Jewelers and Precious Stone and Metal Workers'),
    'jeweller': ('51-9071.00', 'Jewelers and Precious Stone and Metal Workers'),
    'potter': ('51-9195.05', 'Potters, Manufacturing'),
    'glass blower': ('51-9195.04', 'Glass Blowers, Molders, Benders, and Finishers'),
    'baker': ('51-3011.00', 'Bakers'),
    'butcher': ('51-3021.00', 'Butchers and Meat Cutters'),
    'tailor': ('51-6052.00', 'Tailors, Dressmakers, and Custom Sewers'),
    'carpenter': ('47-2031.00', 'Carpenters'),
    'mason': ('47-2021.00', 'Brickmasons and Blockmasons'),
    'plumber': ('47-2152.00', 'Plumbers, Pipefitters, and Steamfitters'),
    'electrician': ('47-2111.00', 'Electricians'),
    
    # -------------------------------------------------------------------------
    # Plant/Factory Operators
    # -------------------------------------------------------------------------
    'plant operator': ('51-8099.00', 'Plant and System Operators, All Other'),
    'machine operator': ('51-9199.00', 'Production Workers, All Other'),
    'factory': ('51-9199.00', 'Production Workers, All Other'),
    'manufacturing': ('51-9199.00', 'Production Workers, All Other'),
    'glass plant': ('51-9195.04', 'Glass Blowers, Molders, Benders, and Finishers'),
    'ceramic plant': ('51-9195.00', 'Molders, Shapers, and Casters, Except Metal and Plastic'),
    
    # -------------------------------------------------------------------------
    # Service Workers
    # -------------------------------------------------------------------------
    'waiter': ('35-3031.00', 'Waiters and Waitresses'),
    'cook': ('35-2014.00', 'Cooks, Restaurant'),
    'chef': ('35-1011.00', 'Chefs and Head Cooks'),
    'barber': ('39-5011.00', 'Barbers'),
    'hairdresser': ('39-5012.00', 'Hairdressers, Hairstylists, and Cosmetologists'),
    'beautician': ('39-5012.00', 'Hairdressers, Hairstylists, and Cosmetologists'),
    
    # -------------------------------------------------------------------------
    # Security/Protection
    # -------------------------------------------------------------------------
    'police': ('33-3051.00', "Police and Sheriff's Patrol Officers"),
    'constable': ('33-3051.00', "Police and Sheriff's Patrol Officers"),
    'guard': ('33-9032.00', 'Security Guards'),
    'watchman': ('33-9032.00', 'Security Guards'),
    'security': ('33-9032.00', 'Security Guards'),
    'firefighter': ('33-2011.00', 'Firefighters'),
    'fireman': ('33-2011.00', 'Firefighters'),
    
    # -------------------------------------------------------------------------
    # Service - Hospitality
    # -------------------------------------------------------------------------
    'porter': ('39-6011.00', 'Baggage Porters and Bellhops'),
    'bellhop': ('39-6011.00', 'Baggage Porters and Bellhops'),
    'doorkeeper': ('39-6011.00', 'Baggage Porters and Bellhops'),
    'concierge': ('39-6012.00', 'Concierges'),
    
    # -------------------------------------------------------------------------
    # Clerical/Administrative
    # -------------------------------------------------------------------------
    'clerk': ('43-9061.00', 'Office Clerks, General'),
    'secretary': ('43-6014.00', 'Secretaries and Administrative Assistants, Except Legal, Medical, and Executive'),
    'typist': ('43-9022.00', 'Word Processors and Typists'),
    'receptionist': ('43-4171.00', 'Receptionists and Information Clerks'),
    'cashier': ('41-2011.00', 'Cashiers'),
    'accountant': ('13-2011.00', 'Accountants and Auditors'),
    'auditor': ('13-2011.00', 'Accountants and Auditors'),
    
    # -------------------------------------------------------------------------
    # Mining/Extraction
    # -------------------------------------------------------------------------
    'miner': ('47-5041.00', 'Continuous Mining Machine Operators'),
    'quarry': ('47-5041.00', 'Continuous Mining Machine Operators'),
    'driller': ('47-5012.00', 'Rotary Drill Operators, Oil and Gas'),
    
    # -------------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------------
    'concrete': ('47-2051.00', 'Cement Masons and Concrete Finishers'),
    'mould': ('51-4071.00', 'Foundry Mold and Coremakers'),
    'moulder': ('51-4071.00', 'Foundry Mold and Coremakers'),
}


# =============================================================================
# NCO PREFIX TO O*NET FALLBACK MAPPINGS
# =============================================================================
# These provide fallback mappings based on the NCO hierarchical code structure.
# The first 4 digits of NCO codes indicate the occupational unit group.

NCO_PREFIX_DEFAULTS: Dict[str, Tuple[str, str]] = {
    # -------------------------------------------------------------------------
    # Division 1: Managers
    # -------------------------------------------------------------------------
    '1111': ('11-1031.00', 'Legislators'),
    '1112': ('11-1011.00', 'Chief Executives'),
    '1113': ('11-1011.00', 'Chief Executives'),
    '1114': ('11-1011.00', 'Chief Executives'),
    '1120': ('11-1011.00', 'Chief Executives'),
    '1211': ('11-3031.00', 'Financial Managers'),
    '1212': ('11-3121.00', 'Human Resources Managers'),
    '1213': ('11-1021.00', 'General and Operations Managers'),
    '1219': ('11-1021.00', 'General and Operations Managers'),
    '1221': ('11-2022.00', 'Sales Managers'),
    '1222': ('11-2011.00', 'Advertising and Promotions Managers'),
    '1223': ('11-9041.00', 'Architectural and Engineering Managers'),
    '1311': ('11-9013.00', 'Farmers, Ranchers, and Other Agricultural Managers'),
    '1312': ('11-9013.00', 'Farmers, Ranchers, and Other Agricultural Managers'),
    '1321': ('11-3051.00', 'Industrial Production Managers'),
    '1322': ('11-9041.00', 'Architectural and Engineering Managers'),
    '1323': ('11-9021.00', 'Construction Managers'),
    '1324': ('11-3071.00', 'Transportation, Storage, and Distribution Managers'),
    '1330': ('11-3021.00', 'Computer and Information Systems Managers'),
    '1341': ('11-9031.00', 'Education and Childcare Administrators, Preschool and Daycare'),
    '1342': ('11-9111.00', 'Medical and Health Services Managers'),
    '1343': ('11-9111.00', 'Medical and Health Services Managers'),
    '1344': ('11-9151.00', 'Social and Community Service Managers'),
    '1345': ('11-9032.00', 'Education Administrators, Kindergarten through Secondary'),
    '1346': ('11-3031.00', 'Financial Managers'),
    '1349': ('11-1021.00', 'General and Operations Managers'),
    '1411': ('11-9081.00', 'Lodging Managers'),
    '1412': ('11-9051.00', 'Food Service Managers'),
    '1420': ('11-1021.00', 'General and Operations Managers'),
    '1431': ('11-9072.00', 'Entertainment and Recreation Managers, Except Gambling'),
    '1439': ('11-1021.00', 'General and Operations Managers'),
    
    # -------------------------------------------------------------------------
    # Division 2: Professionals
    # -------------------------------------------------------------------------
    '2111': ('19-2012.00', 'Physicists'),
    '2112': ('19-2021.00', 'Atmospheric and Space Scientists'),
    '2113': ('19-2031.00', 'Chemists'),
    '2114': ('19-2042.00', 'Geoscientists, Except Hydrologists and Geographers'),
    '2120': ('15-2041.00', 'Statisticians'),
    '2131': ('19-1029.04', 'Biologists'),
    '2132': ('19-1031.00', 'Conservation Scientists'),
    '2133': ('19-2041.00', 'Environmental Scientists and Specialists, Including Health'),
    '2141': ('17-2112.00', 'Industrial Engineers'),
    '2142': ('17-2051.00', 'Civil Engineers'),
    '2143': ('17-2081.00', 'Environmental Engineers'),
    '2144': ('17-2141.00', 'Mechanical Engineers'),
    '2145': ('17-2041.00', 'Chemical Engineers'),
    '2146': ('17-2151.00', 'Mining and Geological Engineers, Including Mining Safety Engineers'),
    '2149': ('17-2199.00', 'Engineers, All Other'),
    '2151': ('17-2071.00', 'Electrical Engineers'),
    '2152': ('17-2072.00', 'Electronics Engineers, Except Computer'),
    '2153': ('17-2072.00', 'Electronics Engineers, Except Computer'),
    '2161': ('17-1011.00', 'Architects, Except Landscape and Naval'),
    '2162': ('17-1012.00', 'Landscape Architects'),
    '2163': ('27-1021.00', 'Commercial and Industrial Designers'),
    '2164': ('19-3051.00', 'Urban and Regional Planners'),
    '2165': ('17-1021.00', 'Cartographers and Photogrammetrists'),
    '2166': ('27-1024.00', 'Graphic Designers'),
    '2211': ('29-1216.00', 'General Internal Medicine Physicians'),
    '2212': ('29-1229.00', 'Physicians, All Other'),
    '2221': ('29-1141.00', 'Registered Nurses'),
    '2222': ('29-9099.01', 'Midwives'),
    '2230': ('29-1291.00', 'Acupuncturists'),
    '2240': ('29-2041.00', 'Emergency Medical Technicians'),
    '2250': ('29-1131.00', 'Veterinarians'),
    '2261': ('29-1021.00', 'Dentists, General'),
    '2262': ('29-1051.00', 'Pharmacists'),
    '2263': ('19-2041.00', 'Environmental Scientists and Specialists, Including Health'),
    '2264': ('29-1123.00', 'Physical Therapists'),
    '2265': ('29-1031.00', 'Dietitians and Nutritionists'),
    '2266': ('29-1181.00', 'Audiologists'),
    '2267': ('29-1041.00', 'Optometrists'),
    '2269': ('29-1299.00', 'Healthcare Diagnosing or Treating Practitioners, All Other'),
    '2310': ('25-1099.00', 'Postsecondary Teachers, All Other'),
    '2320': ('25-1194.00', 'Career/Technical Education Teachers, Postsecondary'),
    '2330': ('25-2031.00', 'Secondary School Teachers, Except Special and Career/Technical Education'),
    '2341': ('25-2021.00', 'Elementary School Teachers, Except Special Education'),
    '2342': ('25-2011.00', 'Preschool Teachers, Except Special Education'),
    '2351': ('25-9031.00', 'Instructional Coordinators'),
    '2352': ('25-2059.00', 'Special Education Teachers, All Other'),
    '2353': ('25-3011.00', 'Adult Basic Education, Adult Secondary Education, and English as a Second Language Instructors'),
    '2354': ('25-1121.00', 'Art, Drama, and Music Teachers, Postsecondary'),
    '2355': ('25-1121.00', 'Art, Drama, and Music Teachers, Postsecondary'),
    '2356': ('25-1021.00', 'Computer Science Teachers, Postsecondary'),
    '2359': ('25-3099.00', 'Teachers and Instructors, All Other'),
    '2411': ('13-2011.00', 'Accountants and Auditors'),
    '2412': ('13-2051.00', 'Financial and Investment Analysts'),
    '2413': ('13-2051.00', 'Financial and Investment Analysts'),
    '2421': ('13-1111.00', 'Management Analysts'),
    '2422': ('13-1111.00', 'Management Analysts'),
    '2423': ('13-1071.00', 'Human Resources Specialists'),
    '2424': ('13-1151.00', 'Training and Development Specialists'),
    '2431': ('13-1161.00', 'Market Research Analysts and Marketing Specialists'),
    '2432': ('27-3031.00', 'Public Relations Specialists'),
    '2433': ('41-4011.00', 'Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products'),
    '2434': ('41-4011.00', 'Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products'),
    '2511': ('15-1211.00', 'Computer Systems Analysts'),
    '2512': ('15-1252.00', 'Software Developers'),
    '2513': ('15-1254.00', 'Web Developers'),
    '2514': ('15-1251.00', 'Computer Programmers'),
    '2519': ('15-1299.00', 'Computer Occupations, All Other'),
    '2521': ('15-1242.00', 'Database Administrators'),
    '2522': ('15-1244.00', 'Network and Computer Systems Administrators'),
    '2523': ('15-1241.00', 'Computer Network Architects'),
    '2529': ('15-1299.00', 'Computer Occupations, All Other'),
    '2611': ('23-1011.00', 'Lawyers'),
    '2612': ('23-1023.00', 'Judges, Magistrate Judges, and Magistrates'),
    '2619': ('23-1011.00', 'Lawyers'),
    '2621': ('25-4011.00', 'Archivists'),
    '2622': ('25-4022.00', 'Librarians and Media Collections Specialists'),
    '2631': ('19-3011.00', 'Economists'),
    '2632': ('19-3041.00', 'Sociologists'),
    '2633': ('25-1126.00', 'Philosophy and Religion Teachers, Postsecondary'),
    '2634': ('19-3031.00', 'Psychologists, All Other'),
    '2635': ('21-1029.00', 'Social Workers, All Other'),
    '2636': ('21-2011.00', 'Clergy'),
    '2641': ('27-3043.00', 'Writers and Authors'),
    '2642': ('27-3023.00', 'News Analysts, Reporters, and Journalists'),
    '2643': ('27-3091.00', 'Interpreters and Translators'),
    '2651': ('27-1013.00', 'Fine Artists, Including Painters, Sculptors, and Illustrators'),
    '2652': ('27-2042.00', 'Musicians and Singers'),
    '2653': ('27-2031.00', 'Dancers'),
    '2654': ('27-2012.00', 'Producers and Directors'),
    '2655': ('27-2011.00', 'Actors'),
    '2656': ('27-3011.00', 'Broadcast Announcers and Radio Disc Jockeys'),
    '2659': ('27-2099.00', 'Entertainers and Performers, Sports and Related Workers, All Other'),
    
    # -------------------------------------------------------------------------
    # Division 3: Technicians and Associate Professionals
    # -------------------------------------------------------------------------
    '3111': ('19-4031.00', 'Chemical Technicians'),
    '3112': ('17-3022.00', 'Civil Engineering Technologists and Technicians'),
    '3113': ('17-3023.00', 'Electrical and Electronic Engineering Technologists and Technicians'),
    '3114': ('17-3023.00', 'Electrical and Electronic Engineering Technologists and Technicians'),
    '3115': ('17-3027.00', 'Mechanical Engineering Technologists and Technicians'),
    '3116': ('19-4031.00', 'Chemical Technicians'),
    '3117': ('19-4041.00', 'Geological Technicians, Except Hydrologic Technicians'),
    '3118': ('17-3011.00', 'Architectural and Civil Drafters'),
    '3119': ('17-3029.00', 'Engineering Technologists and Technicians, Except Drafters, All Other'),
    '3121': ('47-1011.00', 'First-Line Supervisors of Construction Trades and Extraction Workers'),
    '3122': ('51-1011.00', 'First-Line Supervisors of Production and Operating Workers'),
    '3123': ('47-1011.00', 'First-Line Supervisors of Construction Trades and Extraction Workers'),
    '3131': ('51-8013.00', 'Power Plant Operators'),
    '3132': ('51-8031.00', 'Water and Wastewater Treatment Plant and System Operators'),
    '3133': ('51-8091.00', 'Chemical Plant and System Operators'),
    '3134': ('51-8093.00', 'Petroleum Pump System Operators, Refinery Operators, and Gaugers'),
    '3135': ('51-4051.00', 'Metal-Refining Furnace Operators and Tenders'),
    '3139': ('51-8099.00', 'Plant and System Operators, All Other'),
    '3141': ('19-4021.00', 'Biological Technicians'),
    '3142': ('19-4012.00', 'Agricultural Technicians'),
    '3143': ('19-4071.00', 'Forest and Conservation Technicians'),
    '3151': ('53-5031.00', 'Ship Engineers'),
    '3152': ('53-5021.00', 'Captains, Mates, and Pilots of Water Vessels'),
    '3153': ('53-2011.00', 'Airline Pilots, Copilots, and Flight Engineers'),
    '3154': ('53-2021.00', 'Air Traffic Controllers'),
    '3155': ('49-3011.00', 'Aircraft Mechanics and Service Technicians'),
    '3211': ('29-2034.00', 'Radiologic Technologists and Technicians'),
    '3212': ('29-2012.00', 'Medical and Clinical Laboratory Technicians'),
    '3213': ('29-2052.00', 'Pharmacy Technicians'),
    '3214': ('51-9081.00', 'Dental Laboratory Technicians'),
    '3219': ('29-2099.00', 'Health Technologists and Technicians, All Other'),
    '3221': ('29-2061.00', 'Licensed Practical and Licensed Vocational Nurses'),
    '3222': ('29-9099.01', 'Midwives'),
    '3230': ('29-1299.00', 'Healthcare Diagnosing or Treating Practitioners, All Other'),
    '3240': ('29-2056.00', 'Veterinary Technologists and Technicians'),
    '3251': ('31-9091.00', 'Dental Assistants'),
    '3252': ('29-2072.00', 'Medical Records Specialists'),
    '3253': ('21-1094.00', 'Community Health Workers'),
    '3254': ('29-2081.00', 'Opticians, Dispensing'),
    '3255': ('31-2021.00', 'Physical Therapist Assistants'),
    '3256': ('31-9092.00', 'Medical Assistants'),
    '3257': ('19-4042.00', 'Environmental Science and Protection Technicians, Including Health'),
    '3258': ('29-2042.00', 'Emergency Medical Technicians'),
    '3259': ('31-9099.00', 'Healthcare Support Workers, All Other'),
    '3311': ('41-3031.00', 'Securities, Commodities, and Financial Services Sales Agents'),
    '3312': ('13-2072.00', 'Loan Officers'),
    '3313': ('43-3031.00', 'Bookkeeping, Accounting, and Auditing Clerks'),
    '3314': ('43-9111.00', 'Statistical Assistants'),
    '3315': ('13-2023.00', 'Appraisers and Assessors of Real Estate'),
    '3321': ('41-3021.00', 'Insurance Sales Agents'),
    '3322': ('41-4012.00', 'Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products'),
    '3323': ('13-1022.00', 'Wholesale and Retail Buyers, Except Farm Products'),
    '3324': ('41-3031.00', 'Securities, Commodities, and Financial Services Sales Agents'),
    '3331': ('43-5011.00', 'Cargo and Freight Agents'),
    '3332': ('13-1121.00', 'Meeting, Convention, and Event Planners'),
    '3333': ('13-1071.00', 'Human Resources Specialists'),
    '3334': ('41-9022.00', 'Real Estate Sales Agents'),
    '3339': ('13-1199.00', 'Business Operations Specialists, All Other'),
    '3341': ('43-1011.00', 'First-Line Supervisors of Office and Administrative Support Workers'),
    '3342': ('43-6012.00', 'Legal Secretaries and Administrative Assistants'),
    '3343': ('43-6011.00', 'Executive Secretaries and Executive Administrative Assistants'),
    '3344': ('43-6013.00', 'Medical Secretaries and Administrative Assistants'),
    '3351': ('33-3051.04', 'Customs and Border Protection Officers'),
    '3352': ('13-2081.00', 'Tax Examiners and Collectors, and Revenue Agents'),
    '3353': ('43-4061.00', 'Eligibility Interviewers, Government Programs'),
    '3354': ('43-4031.00', 'Court, Municipal, and License Clerks'),
    '3355': ('33-3021.00', 'Detectives and Criminal Investigators'),
    '3359': ('13-1041.00', 'Compliance Officers'),
    '3411': ('23-2011.00', 'Paralegals and Legal Assistants'),
    '3412': ('21-1093.00', 'Social and Human Service Assistants'),
    '3413': ('21-2099.00', 'Religious Workers, All Other'),
    '3421': ('27-2021.00', 'Athletes and Sports Competitors'),
    '3422': ('27-2022.00', 'Coaches and Scouts'),
    '3423': ('39-9031.00', 'Exercise Trainers and Group Fitness Instructors'),
    '3431': ('27-4021.00', 'Photographers'),
    '3432': ('27-1025.00', 'Interior Designers'),
    '3433': ('25-4013.00', 'Museum Technicians and Conservators'),
    '3434': ('35-1011.00', 'Chefs and Head Cooks'),
    '3435': ('27-1019.00', 'Artists and Related Workers, All Other'),
    '3511': ('15-1232.00', 'Computer User Support Specialists'),
    '3512': ('15-1232.00', 'Computer User Support Specialists'),
    '3513': ('15-1231.00', 'Computer Network Support Specialists'),
    '3514': ('15-1254.00', 'Web Developers'),
    '3521': ('27-4011.00', 'Audio and Video Technicians'),
    '3522': ('49-2022.00', 'Telecommunications Equipment Installers and Repairers, Except Line Installers'),
    
    # -------------------------------------------------------------------------
    # Division 4: Clerical Support Workers
    # -------------------------------------------------------------------------
    '4110': ('43-9061.00', 'Office Clerks, General'),
    '4120': ('43-6014.00', 'Secretaries and Administrative Assistants, Except Legal, Medical, and Executive'),
    '4131': ('43-9022.00', 'Word Processors and Typists'),
    '4132': ('43-9021.00', 'Data Entry Keyers'),
    '4211': ('43-3071.00', 'Tellers'),
    '4212': ('43-3041.00', 'Gambling Cage Workers'),
    '4213': ('13-2072.00', 'Loan Officers'),
    '4214': ('43-3011.00', 'Bill and Account Collectors'),
    '4221': ('41-3041.00', 'Travel Agents'),
    '4222': ('43-4051.00', 'Customer Service Representatives'),
    '4223': ('43-2021.00', 'Telephone Operators'),
    '4224': ('43-4081.00', 'Hotel, Motel, and Resort Desk Clerks'),
    '4225': ('43-4171.00', 'Receptionists and Information Clerks'),
    '4226': ('43-4171.00', 'Receptionists and Information Clerks'),
    '4227': ('43-4111.00', 'Interviewers, Except Eligibility and Loan'),
    '4229': ('43-4199.00', 'Information and Record Clerks, All Other'),
    '4311': ('43-3031.00', 'Bookkeeping, Accounting, and Auditing Clerks'),
    '4312': ('43-9111.00', 'Statistical Assistants'),
    '4313': ('43-3051.00', 'Payroll and Timekeeping Clerks'),
    '4321': ('43-5071.00', 'Shipping, Receiving, and Inventory Clerks'),
    '4322': ('43-5061.00', 'Production, Planning, and Expediting Clerks'),
    '4323': ('43-5011.00', 'Cargo and Freight Agents'),
    '4411': ('43-4121.00', 'Library Assistants, Clerical'),
    '4412': ('43-9051.00', 'Mail Clerks and Mail Machine Operators, Except Postal Service'),
    '4413': ('43-9081.00', 'Proofreaders and Copy Markers'),
    '4414': ('43-9022.00', 'Word Processors and Typists'),
    '4415': ('43-4071.00', 'File Clerks'),
    '4416': ('43-4161.00', 'Human Resources Assistants, Except Payroll and Timekeeping'),
    '4419': ('43-9199.00', 'Office and Administrative Support Workers, All Other'),
    
    # -------------------------------------------------------------------------
    # Division 5: Service and Sales Workers
    # -------------------------------------------------------------------------
    '5111': ('53-2031.00', 'Flight Attendants'),
    '5112': ('53-4031.00', 'Railroad Conductors and Yardmasters'),
    '5113': ('39-7011.00', 'Tour Guides and Escorts'),
    '5120': ('35-2014.00', 'Cooks, Restaurant'),
    '5131': ('35-3031.00', 'Waiters and Waitresses'),
    '5132': ('35-3011.00', 'Bartenders'),
    '5141': ('39-5012.00', 'Hairdressers, Hairstylists, and Cosmetologists'),
    '5142': ('39-5012.00', 'Hairdressers, Hairstylists, and Cosmetologists'),
    '5151': ('37-2011.00', 'Janitors and Cleaners, Except Maids and Housekeeping Cleaners'),
    '5152': ('37-2012.00', 'Maids and Housekeeping Cleaners'),
    '5153': ('37-1011.00', 'First-Line Supervisors of Housekeeping and Janitorial Workers'),
    '5161': ('39-9099.00', 'Personal Care and Service Workers, All Other'),
    '5162': ('39-9099.00', 'Personal Care and Service Workers, All Other'),
    '5163': ('39-4031.00', 'Morticians, Undertakers, and Funeral Arrangers'),
    '5164': ('39-2021.00', 'Animal Caretakers'),
    '5165': ('25-3021.00', 'Self-Enrichment Teachers'),
    '5169': ('39-9099.00', 'Personal Care and Service Workers, All Other'),
    '5211': ('41-2031.00', 'Retail Salespersons'),
    '5212': ('41-9091.00', 'Door-to-Door Sales Workers, News and Street Vendors, and Related Workers'),
    '5221': ('41-1011.00', 'First-Line Supervisors of Retail Sales Workers'),
    '5222': ('41-1011.00', 'First-Line Supervisors of Retail Sales Workers'),
    '5223': ('41-2031.00', 'Retail Salespersons'),
    '5230': ('41-2011.00', 'Cashiers'),
    '5241': ('41-9012.00', 'Models'),
    '5242': ('41-9011.00', 'Demonstrators and Product Promoters'),
    '5243': ('41-9091.00', 'Door-to-Door Sales Workers, News and Street Vendors, and Related Workers'),
    '5244': ('41-9041.00', 'Telemarketers'),
    '5245': ('53-6031.00', 'Automotive and Watercraft Service Attendants'),
    '5246': ('35-3023.00', 'Fast Food and Counter Workers'),
    '5249': ('41-9099.00', 'Sales and Related Workers, All Other'),
    '5311': ('39-9011.00', 'Childcare Workers'),
    '5312': ('25-9042.00', 'Teaching Assistants, Preschool, Elementary, Middle, and Secondary School, Except Special Education'),
    '5321': ('31-1121.00', 'Home Health Aides'),
    '5322': ('31-1122.00', 'Personal Care Aides'),
    '5329': ('31-9099.00', 'Healthcare Support Workers, All Other'),
    '5411': ('33-2011.00', 'Firefighters'),
    '5412': ('33-3051.00', "Police and Sheriff's Patrol Officers"),
    '5413': ('33-3012.00', 'Correctional Officers and Jailers'),
    '5414': ('33-9032.00', 'Security Guards'),
    '5419': ('33-9099.00', 'Protective Service Workers, All Other'),
    
    # -------------------------------------------------------------------------
    # Division 6: Skilled Agricultural, Forestry and Fishery Workers
    # -------------------------------------------------------------------------
    '6111': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    '6112': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    '6113': ('37-3011.00', 'Landscaping and Groundskeeping Workers'),
    '6114': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    '6121': ('45-2021.00', 'Animal Breeders'),
    '6122': ('45-2093.00', 'Farmworkers, Farm, Ranch, and Aquacultural Animals'),
    '6123': ('45-2093.00', 'Farmworkers, Farm, Ranch, and Aquacultural Animals'),
    '6129': ('45-2093.00', 'Farmworkers, Farm, Ranch, and Aquacultural Animals'),
    '6130': ('45-2093.00', 'Farmworkers, Farm, Ranch, and Aquacultural Animals'),
    '6210': ('45-4011.00', 'Forest and Conservation Workers'),
    '6221': ('45-3031.00', 'Fishing and Hunting Workers'),
    '6222': ('45-3031.00', 'Fishing and Hunting Workers'),
    '6223': ('45-3031.00', 'Fishing and Hunting Workers'),
    '6224': ('45-3031.00', 'Fishing and Hunting Workers'),
    
    # -------------------------------------------------------------------------
    # Division 7: Craft and Related Trades Workers
    # -------------------------------------------------------------------------
    '7111': ('47-2061.00', 'Construction Laborers'),
    '7112': ('47-2021.00', 'Brickmasons and Blockmasons'),
    '7113': ('47-2022.00', 'Stonemasons'),
    '7114': ('47-2051.00', 'Cement Masons and Concrete Finishers'),
    '7115': ('47-2031.00', 'Carpenters'),
    '7119': ('47-2061.00', 'Construction Laborers'),
    '7121': ('47-2181.00', 'Roofers'),
    '7122': ('47-2044.00', 'Tile and Stone Setters'),
    '7123': ('47-2161.00', 'Plasterers and Stucco Masons'),
    '7124': ('47-2131.00', 'Insulation Workers, Floor, Ceiling, and Wall'),
    '7125': ('47-2121.00', 'Glaziers'),
    '7126': ('47-2152.00', 'Plumbers, Pipefitters, and Steamfitters'),
    '7127': ('49-9021.00', 'Heating, Air Conditioning, and Refrigeration Mechanics and Installers'),
    '7131': ('47-2141.00', 'Painters, Construction and Maintenance'),
    '7132': ('51-9124.00', 'Coating, Painting, and Spraying Machine Setters, Operators, and Tenders'),
    '7133': ('37-2011.00', 'Janitors and Cleaners, Except Maids and Housekeeping Cleaners'),
    '7211': ('51-4071.00', 'Foundry Mold and Coremakers'),
    '7212': ('51-4121.00', 'Welders, Cutters, Solderers, and Brazers'),
    '7213': ('47-2211.00', 'Sheet Metal Workers'),
    '7214': ('51-2041.00', 'Structural Metal Fabricators and Fitters'),
    '7215': ('49-9096.00', 'Riggers'),
    '7221': ('51-4199.00', 'Metal Workers and Plastic Workers, All Other'),
    '7222': ('51-4111.00', 'Tool and Die Makers'),
    '7223': ('51-4041.00', 'Machinists'),
    '7224': ('51-4033.00', 'Grinding, Lapping, Polishing, and Buffing Machine Tool Setters, Operators, and Tenders, Metal and Plastic'),
    '7231': ('49-3023.00', 'Automotive Service Technicians and Mechanics'),
    '7232': ('49-3011.00', 'Aircraft Mechanics and Service Technicians'),
    '7233': ('49-3041.00', 'Farm Equipment Mechanics and Service Technicians'),
    '7234': ('49-3091.00', 'Bicycle Repairers'),
    '7311': ('49-9064.00', 'Watch and Clock Repairers'),
    '7312': ('49-9063.00', 'Musical Instrument Repairers and Tuners'),
    '7313': ('51-9071.00', 'Jewelers and Precious Stone and Metal Workers'),
    '7314': ('51-9195.05', 'Potters, Manufacturing'),
    '7315': ('51-9195.04', 'Glass Blowers, Molders, Benders, and Finishers'),
    '7316': ('27-1024.00', 'Graphic Designers'),
    '7317': ('51-7099.00', 'Woodworkers, All Other'),
    '7318': ('51-6099.00', 'Textile, Apparel, and Furnishings Workers, All Other'),
    '7319': ('51-9199.00', 'Production Workers, All Other'),
    '7321': ('51-5111.00', 'Prepress Technicians and Workers'),
    '7322': ('51-5112.00', 'Printing Press Operators'),
    '7323': ('51-5113.00', 'Print Binding and Finishing Workers'),
    '7411': ('47-2111.00', 'Electricians'),
    '7412': ('49-2092.00', 'Electric Motor, Power Tool, and Related Repairers'),
    '7413': ('49-9051.00', 'Electrical Power-Line Installers and Repairers'),
    '7421': ('49-2094.00', 'Electrical and Electronics Repairers, Commercial and Industrial Equipment'),
    '7422': ('49-2022.00', 'Telecommunications Equipment Installers and Repairers, Except Line Installers'),
    '7511': ('51-3021.00', 'Butchers and Meat Cutters'),
    '7512': ('51-3011.00', 'Bakers'),
    '7513': ('51-3092.00', 'Food Batchmakers'),
    '7514': ('51-3092.00', 'Food Batchmakers'),
    '7515': ('19-4013.00', 'Food Science Technicians'),
    '7516': ('51-3091.00', 'Food and Tobacco Roasting, Baking, and Drying Machine Operators and Tenders'),
    '7521': ('51-7011.00', 'Cabinetmakers and Bench Carpenters'),
    '7522': ('51-7011.00', 'Cabinetmakers and Bench Carpenters'),
    '7523': ('51-7042.00', 'Woodworking Machine Setters, Operators, and Tenders, Except Sawing'),
    '7531': ('51-6052.00', 'Tailors, Dressmakers, and Custom Sewers'),
    '7532': ('51-6062.00', 'Textile Cutting Machine Setters, Operators, and Tenders'),
    '7533': ('51-6031.00', 'Sewing Machine Operators'),
    '7534': ('51-6093.00', 'Upholsterers'),
    '7535': ('51-6099.00', 'Textile, Apparel, and Furnishings Workers, All Other'),
    '7536': ('51-6041.00', 'Shoe and Leather Workers and Repairers'),
    '7541': ('49-9092.00', 'Commercial Divers'),
    '7542': ('47-5032.00', 'Explosives Workers, Ordnance Handling Experts, and Blasters'),
    '7543': ('51-9061.00', 'Inspectors, Testers, Sorters, Samplers, and Weighers'),
    '7544': ('37-2021.00', 'Pest Control Workers'),
    '7549': ('51-9199.00', 'Production Workers, All Other'),
    
    # -------------------------------------------------------------------------
    # Division 8: Plant and Machine Operators, and Assemblers
    # -------------------------------------------------------------------------
    '8111': ('47-5041.00', 'Continuous Mining Machine Operators'),
    '8112': ('51-9021.00', 'Crushing, Grinding, and Polishing Machine Setters, Operators, and Tenders'),
    '8113': ('47-5012.00', 'Rotary Drill Operators, Oil and Gas'),
    '8114': ('51-9023.00', 'Mixing and Blending Machine Setters, Operators, and Tenders'),
    '8121': ('51-4051.00', 'Metal-Refining Furnace Operators and Tenders'),
    '8122': ('51-4193.00', 'Plating Machine Setters, Operators, and Tenders, Metal and Plastic'),
    '8131': ('51-9011.00', 'Chemical Equipment Operators and Tenders'),
    '8132': ('51-9151.00', 'Photographic Process Workers and Processing Machine Operators'),
    '8141': ('51-9041.00', 'Extruding, Forming, Pressing, and Compacting Machine Setters, Operators, and Tenders'),
    '8142': ('51-4021.00', 'Extruding and Drawing Machine Setters, Operators, and Tenders, Metal and Plastic'),
    '8143': ('51-9196.00', 'Paper Goods Machine Setters, Operators, and Tenders'),
    '8151': ('51-6063.00', 'Textile Knitting and Weaving Machine Setters, Operators, and Tenders'),
    '8152': ('51-6063.00', 'Textile Knitting and Weaving Machine Setters, Operators, and Tenders'),
    '8153': ('51-6031.00', 'Sewing Machine Operators'),
    '8154': ('51-6061.00', 'Textile Bleaching and Dyeing Machine Operators and Tenders'),
    '8155': ('51-6099.00', 'Textile, Apparel, and Furnishings Workers, All Other'),
    '8156': ('51-6042.00', 'Shoe Machine Operators and Tenders'),
    '8157': ('51-6011.00', 'Laundry and Dry-Cleaning Workers'),
    '8159': ('51-6099.00', 'Textile, Apparel, and Furnishings Workers, All Other'),
    '8160': ('51-3092.00', 'Food Batchmakers'),
    '8171': ('51-9196.00', 'Paper Goods Machine Setters, Operators, and Tenders'),
    '8172': ('51-7041.00', 'Sawing Machine Setters, Operators, and Tenders, Wood'),
    '8181': ('51-9195.04', 'Glass Blowers, Molders, Benders, and Finishers'),
    '8182': ('51-8021.00', 'Stationary Engineers and Boiler Operators'),
    '8183': ('51-9111.00', 'Packaging and Filling Machine Operators and Tenders'),
    '8189': ('51-8099.00', 'Plant and System Operators, All Other'),
    '8211': ('51-2031.00', 'Engine and Other Machine Assemblers'),
    '8212': ('51-2022.00', 'Electrical and Electronic Equipment Assemblers'),
    '8219': ('51-2099.00', 'Assemblers and Fabricators, All Other'),
    '8311': ('53-4011.00', 'Locomotive Engineers'),
    '8312': ('53-4022.00', 'Railroad Brake, Signal, and Switch Operators and Locomotive Firers'),
    '8321': ('53-3054.00', 'Taxi Drivers'),
    '8322': ('53-3054.00', 'Taxi Drivers'),
    '8331': ('53-3052.00', 'Bus Drivers, Transit and Intercity'),
    '8332': ('53-3032.00', 'Heavy and Tractor-Trailer Truck Drivers'),
    '8341': ('45-2091.00', 'Agricultural Equipment Operators'),
    '8342': ('47-2073.00', 'Operating Engineers and Other Construction Equipment Operators'),
    '8343': ('53-7021.00', 'Crane and Tower Operators'),
    '8344': ('53-7051.00', 'Industrial Truck and Tractor Operators'),
    '8350': ('53-5011.00', 'Sailors and Marine Oilers'),
    
    # -------------------------------------------------------------------------
    # Division 9: Elementary Occupations
    # -------------------------------------------------------------------------
    '9111': ('37-2012.00', 'Maids and Housekeeping Cleaners'),
    '9112': ('37-2011.00', 'Janitors and Cleaners, Except Maids and Housekeeping Cleaners'),
    '9121': ('51-6011.00', 'Laundry and Dry-Cleaning Workers'),
    '9122': ('53-7061.00', 'Cleaners of Vehicles and Equipment'),
    '9123': ('37-2011.00', 'Janitors and Cleaners, Except Maids and Housekeeping Cleaners'),
    '9129': ('37-2019.00', 'Building Cleaning Workers, All Other'),
    '9211': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    '9212': ('45-2093.00', 'Farmworkers, Farm, Ranch, and Aquacultural Animals'),
    '9213': ('45-2092.00', 'Farmworkers and Laborers, Crop, Nursery, and Greenhouse'),
    '9214': ('37-3011.00', 'Landscaping and Groundskeeping Workers'),
    '9215': ('45-4011.00', 'Forest and Conservation Workers'),
    '9216': ('45-3031.00', 'Fishing and Hunting Workers'),
    '9311': ('47-5099.00', 'Extraction Workers, All Other'),
    '9312': ('47-2061.00', 'Construction Laborers'),
    '9313': ('47-2061.00', 'Construction Laborers'),
    '9321': ('53-7064.00', 'Packers and Packagers, Hand'),
    '9329': ('51-9199.00', 'Production Workers, All Other'),
    '9331': ('53-7062.00', 'Laborers and Freight, Stock, and Material Movers, Hand'),
    '9332': ('53-7065.00', 'Stockers and Order Fillers'),
    '9333': ('53-7062.00', 'Laborers and Freight, Stock, and Material Movers, Hand'),
    '9334': ('53-7065.00', 'Stockers and Order Fillers'),
    '9411': ('35-2021.00', 'Food Preparation Workers'),
    '9412': ('35-9021.00', 'Dishwashers'),
    '9510': ('41-9091.00', 'Door-to-Door Sales Workers, News and Street Vendors, and Related Workers'),
    '9520': ('41-9091.00', 'Door-to-Door Sales Workers, News and Street Vendors, and Related Workers'),
    '9611': ('53-7081.00', 'Refuse and Recyclable Material Collectors'),
    '9612': ('53-7062.04', 'Recycling and Reclamation Workers'),
    '9613': ('37-2011.00', 'Janitors and Cleaners, Except Maids and Housekeeping Cleaners'),
    '9621': ('39-6011.00', 'Baggage Porters and Bellhops'),
    '9622': ('49-9071.00', 'Maintenance and Repair Workers, General'),
    '9623': ('43-5041.00', 'Meter Readers, Utilities'),
    '9624': ('53-7199.00', 'Material Moving Workers, All Other'),
    '9629': ('39-6011.00', 'Baggage Porters and Bellhops'),
}

# Division-level fallback defaults
DIVISION_DEFAULTS: Dict[str, Tuple[str, str]] = {
    '1': ('11-1021.00', 'General and Operations Managers'),
    '2': ('19-4099.00', 'Life, Physical, and Social Science Technicians, All Other'),
    '3': ('17-3029.00', 'Engineering Technologists and Technicians, Except Drafters, All Other'),
    '4': ('43-9199.00', 'Office and Administrative Support Workers, All Other'),
    '5': ('39-9099.00', 'Personal Care and Service Workers, All Other'),
    '6': ('45-2099.00', 'Agricultural Workers, All Other'),
    '7': ('51-9199.00', 'Production Workers, All Other'),
    '8': ('51-8099.00', 'Plant and System Operators, All Other'),
    '9': ('53-7199.00', 'Material Moving Workers, All Other'),
}


# =============================================================================
# DATA EXTRACTION FUNCTIONS
# =============================================================================

def extract_nco_records(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extract NCO occupation records from the NCO 2015 PDF.
    
    Args:
        pdf_path: Path to the NCO 2015 PDF file
        
    Returns:
        List of dictionaries with keys: nco2015, title, nco2004
    """
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    
    full_text = "\n".join(all_text)
    lines = full_text.split('\n')
    records = []
    
    for line in lines:
        line = line.strip()
        
        # Skip header and metadata lines
        if not line or 'National Classification of Occupations' in line or 'VOLUME' in line:
            continue
        if 'NCO 2015' in line and 'NCO 2004' in line:
            continue
        if line.startswith('Division') or line.startswith('Sub-') or line.startswith('Group') or line.startswith('Family'):
            continue
        
        # Pattern: NCO2015 Title NCO2004
        match = re.match(r'^(\d{4}\.\d{4})\s+(.+?)\s+(\d{4}\.\d{2})$', line)
        if match:
            records.append({
                'nco2015': match.group(1),
                'title': match.group(2).strip(),
                'nco2004': match.group(3)
            })
            continue
        
        # Pattern: NCO2015 Title (no NCO2004)
        match2 = re.match(r'^(\d{4}\.\d{4})\s+(.+)$', line)
        if match2 and not re.search(r'\d{4}\.\d{2}$', line):
            records.append({
                'nco2015': match2.group(1),
                'title': match2.group(2).strip(),
                'nco2004': ''
            })
    
    return records


def extract_onet_records(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extract O*NET occupation records from the O*NET PDF.
    
    Args:
        pdf_path: Path to the O*NET PDF file
        
    Returns:
        List of dictionaries with keys: onet_code, title
    """
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
    
    full_text = "\n".join(all_text)
    lines = full_text.split('\n')
    records = []
    
    for line in lines:
        line = line.strip()
        
        # Skip header and navigation lines
        if not line or 'Job Zone' in line and 'Code' in line and 'Occupation' in line:
            continue
        if 'See All Occupations' in line or 'onetonline.org' in line:
            continue
        if 'Data-level' in line or 'Show Job Zones' in line or 'Show occupations' in line:
            continue
        if 'Save Table' in line or 'Find in list' in line:
            continue
        
        # Pattern variations for O*NET codes
        match = re.match(r'^(?:Not available|\d)?\s*(\d{2}-\d{4}\.\d{2})\s+(.+?)(?:\s+Bright Outlook)?$', line)
        if match:
            records.append({
                'onet_code': match.group(1),
                'title': match.group(2).strip()
            })
            continue
        
        match2 = re.match(r'^(\d)\s+(\d{2}-\d{4}\.\d{2})\s+(.+?)(?:\s+Bright Outlook)?$', line)
        if match2:
            records.append({
                'onet_code': match2.group(2),
                'title': match2.group(3).strip()
            })
            continue
        
        match3 = re.match(r'^Not available\s+(\d{2}-\d{4}\.\d{2})\s+(.+?)(?:\s+Bright Outlook)?$', line)
        if match3:
            records.append({
                'onet_code': match3.group(1),
                'title': match3.group(2).strip()
            })
    
    return records


# =============================================================================
# SEMANTIC MATCHING FUNCTION
# =============================================================================

def find_semantic_match(title: str, nco_code: str) -> Tuple[str, str, int]:
    """
    Find the best O*NET match for an NCO occupation using semantic rules.
    
    The matching process follows this priority:
    1. Check for semantic keyword matches (score: 95)
    2. Use NCO 4-digit prefix fallback (score: 80)
    3. Use NCO 3-digit prefix fallback (score: 75)
    4. Use division-level fallback (score: 60)
    
    Args:
        title: The NCO occupation title
        nco_code: The NCO 2015 code
        
    Returns:
        Tuple of (onet_code, onet_title, match_score)
    """
    title_lower = title.lower()
    
    # Priority 1: Check semantic keyword matches (longest match first)
    sorted_keywords = sorted(SEMANTIC_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in title_lower:
            return SEMANTIC_KEYWORDS[keyword][0], SEMANTIC_KEYWORDS[keyword][1], 95
    
    # Priority 2: Use NCO 4-digit prefix fallback
    prefix = nco_code[:4]
    if prefix in NCO_PREFIX_DEFAULTS:
        return NCO_PREFIX_DEFAULTS[prefix][0], NCO_PREFIX_DEFAULTS[prefix][1], 80
    
    # Priority 3: Try 3-digit prefix with trailing zero
    prefix3 = nco_code[:3] + '0'
    if prefix3 in NCO_PREFIX_DEFAULTS:
        return NCO_PREFIX_DEFAULTS[prefix3][0], NCO_PREFIX_DEFAULTS[prefix3][1], 75
    
    # Priority 4: Division-level fallback
    division = nco_code[0]
    if division in DIVISION_DEFAULTS:
        return DIVISION_DEFAULTS[division][0], DIVISION_DEFAULTS[division][1], 60
    
    return '', '', 0


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def create_crosswalk(nco_pdf: str, onet_pdf: str, output_path: str) -> Dict[str, any]:
    """
    Create the NCO to O*NET crosswalk mapping.
    
    Args:
        nco_pdf: Path to NCO 2015 PDF
        onet_pdf: Path to O*NET PDF
        output_path: Path for output CSV file
        
    Returns:
        Dictionary with statistics about the mapping
    """
    # Extract records
    print("Extracting NCO data...")
    nco_records = extract_nco_records(nco_pdf)
    print(f"Total NCO records: {len(nco_records)}")
    
    print("Extracting O*NET data...")
    onet_records = extract_onet_records(onet_pdf)
    print(f"Total O*NET records: {len(onet_records)}")
    
    # Create mapping
    print("\nCreating semantic crosswalk mapping...")
    mapping = []
    
    for i, nco in enumerate(nco_records):
        onet_code, onet_title, match_score = find_semantic_match(nco['title'], nco['nco2015'])
        mapping.append({
            'NCO_2015_Code': nco['nco2015'],
            'NCO_2004_Code': nco['nco2004'],
            'NCO_Job_Title': nco['title'],
            'ONET_Code': onet_code,
            'ONET_Job_Title': onet_title,
            'Match_Score': match_score
        })
        
        if (i + 1) % 500 == 0:
            print(f"Processed {i+1}/{len(nco_records)} records...")
    
    # Save to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'NCO_2015_Code', 'NCO_2004_Code', 'NCO_Job_Title',
            'ONET_Code', 'ONET_Job_Title', 'Match_Score'
        ])
        writer.writeheader()
        writer.writerows(mapping)
    
    print(f"\nMapping saved to: {output_path}")
    
    # Calculate statistics
    stats = {
        'total_records': len(mapping),
        'semantic_matches': sum(1 for m in mapping if m['Match_Score'] >= 90),
        'prefix_matches': sum(1 for m in mapping if 80 <= m['Match_Score'] < 90),
        'division_matches': sum(1 for m in mapping if 60 <= m['Match_Score'] < 80),
        'low_matches': sum(1 for m in mapping if 0 < m['Match_Score'] < 60),
        'no_matches': sum(1 for m in mapping if m['Match_Score'] == 0),
        'nco2004_coverage': sum(1 for m in mapping if m['NCO_2004_Code']),
    }
    
    return stats


def print_validation_report(stats: Dict[str, any]) -> None:
    """Print a formatted validation report."""
    print("\n" + "=" * 70)
    print("VALIDATION REPORT - NCO TO O*NET SEMANTIC CROSSWALK")
    print("=" * 70)
    
    total = stats['total_records']
    
    print(f"\nTotal records: {total}")
    print(f"\nMatching Quality:")
    print(f"  Semantic keyword match (>=90): {stats['semantic_matches']} ({100*stats['semantic_matches']/total:.1f}%)")
    print(f"  NCO prefix match (80-89): {stats['prefix_matches']} ({100*stats['prefix_matches']/total:.1f}%)")
    print(f"  Division fallback (60-79): {stats['division_matches']} ({100*stats['division_matches']/total:.1f}%)")
    print(f"  Low confidence (<60): {stats['low_matches']} ({100*stats['low_matches']/total:.1f}%)")
    print(f"  No match: {stats['no_matches']} ({100*stats['no_matches']/total:.1f}%)")
    print(f"\nNCO 2004 Coverage: {stats['nco2004_coverage']} ({100*stats['nco2004_coverage']/total:.1f}%)")
    print("=" * 70)


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Create NCO to O*NET occupation crosswalk mapping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python nco_onet_crosswalk.py --nco nco_2015.pdf --onet onet.pdf --output crosswalk.csv
    python nco_onet_crosswalk.py -n nco_2015.pdf -o onet.pdf -out crosswalk.csv
        """
    )
    
    parser.add_argument(
        '--nco', '-n',
        required=True,
        help='Path to NCO 2015 PDF file'
    )
    
    parser.add_argument(
        '--onet', '-o',
        required=True,
        help='Path to O*NET occupation list PDF file'
    )
    
    parser.add_argument(
        '--output', '-out',
        default='nco_onet_crosswalk.csv',
        help='Output CSV file path (default: nco_onet_crosswalk.csv)'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.nco):
        print(f"Error: NCO PDF file not found: {args.nco}")
        return 1
    
    if not os.path.exists(args.onet):
        print(f"Error: O*NET PDF file not found: {args.onet}")
        return 1
    
    # Create crosswalk
    stats = create_crosswalk(args.nco, args.onet, args.output)
    print_validation_report(stats)
    
    return 0


if __name__ == '__main__':
    exit(main())
