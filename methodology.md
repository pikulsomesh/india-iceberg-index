# Iceberg Index for India: Methodology

## Executive Summary

This document provides functionality for calculating the Iceberg Index at India's district level using:

1. **PLFS 2024 Microdata** - Person-level (cperv1) and Household-level (chhv1) files
2. **NCO-O*NET-AI Automatability Mapping** - 3,445 occupation codes with Felten et al. AIOE scores
3. **District Code Reference** - 694 districts across 36 states/UTs

The Iceberg Index measures the wage-weighted share of occupational skills that AI systems can technically perform, providing a forward-looking indicator of workforce exposure.

---

## 1. Data Sources Overview

### 1.1 Available Data Files

| File | Records | Key Variables | Purpose |
|------|---------|---------------|---------|
| `cperv1.csv` | ~415,549 | Occupation, wages, demographics | Worker-level exposure calculation |
| `chhv1.csv` | ~101,957 | Expenditure, household attributes | Wage proxy for informal workers |
| `nco_onet_automatability.csv` | 3,445 | AI_Automatability (0-100) | Occupation exposure scores |
| `District_codes_PLFS_Panel_4.xlsx` | 694 | State/District names | Geographic labeling |

### 1.2 NCO-O*NET-AI Automatability Dataset for Indian Jobs

**Source:** `data/ai_automability/` and `data/job_code_mapping/`

This project uses a custom mapping pipeline to bridge Indian occupation codes (NCO 2015) with U.S.-based AI exposure data.

#### Sources:
1. **AI Exposure Data**: Sourced from **Felten et al. (2023)**, "How will Language Modelers like ChatGPT Affect Occupations and Industries?". This research provides "Language Modeling AIOE" scores for O*NET occupations.
   - *Location*: `data/ai_automability/nco_onet_automatability.csv`
   - *Logic*: Uses the AIOE methodology which maps 10 AI applications to human abilities.

2. **Job Code Mapping (NCO to O*NET)**:
   - *Source*: PDF Documents from BLS O*NET data and Ministry of Labour and Employment, India ("National Classification of Occupations 2015").
   - *Location*: `data/job_code_mapping/raw/` contains the original PDF reference documents ("national classification of occupations _vol i- 2015.pdf" and "ONet.pdf").
   - *Logic Code*: The mapping logic is implemented in `data/job_code_mapping/files/nco_onet_crosswalk/nco_onet_crosswalk.py`. This script parses the NCO structure and maps it to the closest O*NET equivalents using a hierarchical matching strategy (Direct Match -> Version Mapping -> Base SOC -> Prefix-5).

**Mapping Pipeline Code:**
The complete logic for combining NCO codes with AI scores is provided in:
- `data/ai_automability/create_automatability_mapping.py`

---

## 2. Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ICEBERG INDEX DATA PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1: DATA LOADING & PREPARATION                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   cperv1    │  │   chhv1     │  │ automatab-  │  │  district   │        │
│  │  (Person)   │  │ (Household) │  │    ility    │  │   codes     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         v                v                v                v               │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ • Filter employed workers (status 11-51)                         │       │
│  │ • Create district_id = State_UT_Code + District_Code             │       │
│  │ • Aggregate automatability to 3-digit NCO divisions              │       │
│  │ • Clean district names file (skip header rows)                   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  STAGE 2: WAGE ESTIMATION                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ Hierarchical wage imputation:                                    │       │
│  │ 1. CWS_Earnings_Salaried × 4.33 (weekly → monthly)              │       │
│  │ 2. CWS_Earnings_SelfEmployed × 4.33                             │       │
│  │ 3. Sum(Daily wages) × 4.33                                      │       │
│  │ 4. Monthly_Consumer_Expenditure / Household_Size (from chhv1)   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  STAGE 3: INDEX CALCULATION                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ For each district:                                               │       │
│  │   Iceberg Index = Σ(Employment × Wage × Automatability)         │       │
│  │                   ─────────────────────────────────────          │       │
│  │                        Σ(Employment × Wage)                      │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  STAGE 4: OUTPUT & VISUALIZATION                                            │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ • District-level indices with names                              │       │
│  │ • State aggregates                                               │       │
│  │ • Urban/Rural decomposition                                      │       │
│  │ • Industry concentration (HHI)                                   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The underlying Python implementation processes these stages to generate the district-level indices used in this application.
