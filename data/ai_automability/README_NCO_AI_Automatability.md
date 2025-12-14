# NCO → O*NET → AI Automatability Mapping

## Overview

This dataset maps 3,445 Indian National Classification of Occupations (NCO 2015) codes to AI automatability scores, using Felten et al.'s Language Modeling AIOE methodology.

## Methodology

### Primary Source: Felten et al. (2023)
**"How will Language Modelers like ChatGPT Affect Occupations and Industries?"**

- Uses Language Modeling AIOE (Artificial Intelligence Occupational Exposure) scores
- Based on mapping 10 AI applications to 52 human abilities via crowd-sourced matrix
- Specifically weights language model capabilities (GPT-3, ChatGPT era)
- Original scores range from -1.854 (least exposed) to +1.926 (most exposed)
- Covers 774 U.S. O*NET occupations (2019 vintage)

### Supplementary Framework: Project Iceberg (2025)
The Iceberg Index methodology informed the overall approach:
- Maps 13,000+ AI tools to O*NET skills
- Creates skill-level capability matrices
- Iceberg Index = wage-weighted measure of automatable skills

## Data Pipeline

```
NCO 2015 Code → O*NET Code (via crosswalk) → AIOE Score → Normalized (0-100)
```

### Matching Strategy (hierarchical)

1. **Direct match** (87.6%): Full O*NET code match
2. **Version mapping** (5.0%): O*NET 2023→2019 code conversion
3. **Base SOC** (2.6%): Match on SOC code without suffix
4. **Prefix-5** (4.8%): Average of major occupation group

### O*NET Version Reconciliation

The Felten dataset uses O*NET 2019 codes, while the NCO crosswalk uses O*NET 2023 codes. Key restructurings handled:

| O*NET 2023 | O*NET 2019 | Category |
|------------|------------|----------|
| 15-1211.00 | 15-1121.00 | Computer Systems Analysts |
| 15-1252.00 | 15-1132.00 | Software Developers |
| 15-1254.00 | 15-1134.00 | Web Developers |
| 29-1216.00 | 29-1063.00 | General Internal Medicine Physicians |
| 29-1248.00 | 29-1067.00 | Surgeons, All Other |

(97 total version mappings implemented)

## Score Interpretation

### Normalization
- Original AIOE: -1.854 to +1.926
- Normalized: 0 to 100

### Exposure Categories
| Category | Score Range | Interpretation |
|----------|-------------|----------------|
| Low | 0-25 | Physical/manual tasks, limited AI overlap |
| Medium-Low | 25-50 | Some routine cognitive tasks automatable |
| Medium-High | 50-75 | Significant cognitive task overlap with AI |
| High | 75-100 | Strong AI capability overlap (language/reasoning) |

## Results Summary

### Distribution
| Category | Count | Percentage |
|----------|-------|------------|
| Low | 1,349 | 39.1% |
| Medium-Low | 982 | 28.5% |
| Medium-High | 666 | 19.3% |
| High | 448 | 13.0% |

**Mean Score:** 40.6 (σ = 25.0)

### Highest AI Exposure (Score = 100)
All mapped to "Telemarketers" (SOC 41-9041):
- 5244.01: Operator, Call Centre
- 5244.0101: CRM Domestic Voice
- 5244.0201: CRM Domestic Non-Voice

### Lowest AI Exposure (Score ≈ 1.6-5.2)
- 2653.02/03: Dancers (1.6)
- 7114.xx: Cement Masons, Concrete Workers (4.7)
- 6113.xx: Landscaping/Gardening Workers (5.2)

## Output File Structure

**File:** `nco_onet_automatability.csv`

| Column | Description |
|--------|-------------|
| NCO_2015_Code | India NCO 2015 occupation code |
| NCO_2004_Code | India NCO 2004 occupation code |
| NCO_Job_Title | NCO occupation title |
| ONET_Code | U.S. O*NET occupation code |
| ONET_Job_Title | O*NET occupation title |
| Match_Score | Original crosswalk similarity score |
| LM_AIOE_Raw | Original Felten AIOE score (-1.9 to +1.9) |
| AI_Automatability | Normalized score (0-100) |
| AI_Exposure_Category | Low/Medium-Low/Medium-High/High |
| Match_Type | direct/version_map/base_soc/prefix_5 |

## Limitations

1. **Cross-national mapping**: NCO→O*NET mapping introduces some semantic distance
2. **Temporal gap**: Felten 2023 scores based on GPT-3 era capabilities
3. **Task-level granularity**: Occupation-level scores mask within-occupation variation
4. **India-specific context**: Some Indian occupations may have different task compositions

## References

1. Felten, E., Raj, M., & Seamans, R. (2023). "How will Language Modelers like ChatGPT Affect Occupations and Industries?"

2. Project Iceberg (2025). "The Iceberg Index: Measuring Skills-centered Exposure in the AI Economy." MIT, Oak Ridge National Laboratory. arXiv:2510.25137v2

3. O*NET Resource Center. https://www.onetcenter.org/

4. Ministry of Labour and Employment, India. "National Classification of Occupations 2015."

## Files Included

- `nco_onet_automatability.csv` - Main output (3,445 occupations)
- `create_automatability_mapping.py` - Python implementation
- `README_NCO_AI_Automatability.md` - This documentation
