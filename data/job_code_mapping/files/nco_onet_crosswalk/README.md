# NCO-O*NET Occupation Crosswalk

A semantic mapping tool that creates crosswalks between India's National Classification of Occupations (NCO) 2015/2004 and the US Bureau of Labor Statistics O*NET occupation classification system.

## Overview

This tool addresses the challenge of mapping occupations across different national classification systems. Unlike simple text matching algorithms that can produce incorrect mappings (e.g., matching "mycologist" to "dentist" instead of "biologist"), this tool uses:

1. **Semantic keyword matching** - Domain-specific keywords mapped to appropriate O*NET codes
2. **Hierarchical code structure** - NCO's 4-digit prefix indicates occupational families
3. **Division-level fallbacks** - Broad category defaults when specific matches aren't found

## Features

- Maps 3,445 NCO 2015 occupation codes to O*NET-SOC codes
- Preserves NCO 2015 to NCO 2004 concordance from source documents
- Provides confidence scores (60-95) for each mapping
- Handles India-specific occupations (e.g., Ayurveda practitioners, tabla makers)
- Correctly maps across domains (e.g., university teachers → postsecondary teachers, not elementary)

## Installation

```bash
pip install pdfplumber rapidfuzz
```

## Usage

### Command Line

```bash
python nco_onet_crosswalk.py --nco path/to/nco_2015.pdf --onet path/to/onet.pdf --output crosswalk.csv
```

### As a Module

```python
from nco_onet_crosswalk import create_crosswalk, print_validation_report

stats = create_crosswalk('nco_2015.pdf', 'onet.pdf', 'output.csv')
print_validation_report(stats)
```

## Input Files

1. **NCO 2015 PDF**: "National Classification of Occupations Vol I - 2015" 
   - Contains concordance table with NCO 2015, NCO 2004 codes and job titles
   - Available from: Ministry of Labour and Employment, Government of India

2. **O*NET PDF**: List of O*NET-SOC occupation codes and titles
   - Available from: https://www.onetonline.org/find/all

## Output Format

CSV file with the following columns:

| Column | Description |
|--------|-------------|
| NCO_2015_Code | India's 2015 classification code (format: XXXX.XXXX) |
| NCO_2004_Code | Corresponding 2004 code if available (format: XXXX.XX) |
| NCO_Job_Title | Occupation title from NCO |
| ONET_Code | Matched US O*NET code (format: XX-XXXX.XX) |
| ONET_Job_Title | Occupation title from O*NET |
| Match_Score | Confidence score (60-95) |

### Match Score Interpretation

| Score | Type | Description |
|-------|------|-------------|
| 95 | Semantic keyword | Direct keyword match (e.g., "mycologist" → Biologists) |
| 80 | NCO prefix (4-digit) | Occupational family match (e.g., 2310.* → Postsecondary Teachers) |
| 75 | NCO prefix (3-digit) | Broader group match |
| 60 | Division fallback | Major group default |

## Validation Results

```
======================================================================
VALIDATION REPORT - NCO TO O*NET SEMANTIC CROSSWALK
======================================================================

Total records: 3445

Matching Quality:
  Semantic keyword match (>=90): 1016 (29.5%)
  NCO prefix match (80-89): 2417 (70.2%)
  Division fallback (60-79): 12 (0.3%)
  Low confidence (<60): 0 (0.0%)
  No match: 0 (0.0%)

NCO 2004 Coverage: 2673 (77.6%)
======================================================================
```

## Example Mappings

### Legal Professions
| NCO Title | O*NET Match |
|-----------|-------------|
| Attorney General of India | Lawyers |
| Judge, Supreme Court | Judges, Magistrate Judges, and Magistrates |
| Advocate | Lawyers |

### Higher Education
| NCO Title | O*NET Match |
|-----------|-------------|
| University and College Teacher, Arts | Postsecondary Teachers, All Other |
| Principal, College | Education Administrators, Postsecondary |

### Biological Sciences
| NCO Title | O*NET Match |
|-----------|-------------|
| Mycologist | Biologists |
| Silviculturist | Biologists |
| Anthropologist, Physical | Anthropologists and Archeologists |

### Musical Instruments
| NCO Title | O*NET Match |
|-----------|-------------|
| Tabla Maker | Musical Instrument Repairers and Tuners |
| Harmonium Maker | Musical Instrument Repairers and Tuners |
| Organ Tuner | Musical Instrument Repairers and Tuners |

### Agriculture
| NCO Title | O*NET Match |
|-----------|-------------|
| Rubber Nursery Manager | Farmers, Ranchers, and Other Agricultural Managers |
| Cultivator, General | Farmworkers and Laborers, Crop, Nursery, and Greenhouse |
| Gardener, General | Landscaping and Groundskeeping Workers |

## NCO Code Structure

NCO 2015 follows the ISCO-08 structure:

| Digit(s) | Level | Example |
|----------|-------|---------|
| 1st | Major Group | 2 = Professionals |
| 1-2 | Sub-major Group | 21 = Science and Engineering Professionals |
| 1-3 | Minor Group | 213 = Life Science Professionals |
| 1-4 | Unit Group | 2131 = Biologists, Botanists, Zoologists |
| Full | Occupation | 2131.0700 = Mycologist |

## Methodology

### Semantic Keyword Matching

The tool maintains a dictionary of ~200 domain-specific keywords mapped to O*NET codes. Keywords are matched in order of length (longest first) to ensure specific terms take precedence.

Example:
- "university" → 25-1099.00 (Postsecondary Teachers)
- "mycologist" → 19-1029.04 (Biologists)
- "tabla maker" → 49-9063.00 (Musical Instrument Repairers and Tuners)

### Hierarchical Fallback

When no keyword match is found, the tool uses the NCO code structure:

1. 4-digit prefix lookup (e.g., 2310 → Postsecondary Teachers)
2. 3-digit prefix lookup (e.g., 231 → Teaching Professionals)
3. Division-level default (e.g., 2 → Professionals)

## Limitations

1. **Many-to-one mapping**: Multiple NCO codes may map to the same O*NET code due to different granularity levels (NCO has 3,445 codes vs O*NET's 1,016)

2. **India-specific occupations**: Some occupations have no direct US equivalent (e.g., "Munsif" - a junior civil judge in India)

3. **Not an official crosswalk**: This is a research tool, not an official government concordance

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new keywords or mappings
4. Submit a pull request

## License

MIT License

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{nco_onet_crosswalk,
  title = {NCO-O*NET Occupation Crosswalk},
  year = {2024},
  url = {https://github.com/yourusername/nco-onet-crosswalk}
}
```

## References

1. Ministry of Labour and Employment, Government of India. (2015). *National Classification of Occupations - 2015*. Directorate General of Employment.

2. National Center for O*NET Development. *O*NET OnLine*. https://www.onetonline.org/

3. International Labour Organization. (2012). *International Standard Classification of Occupations (ISCO-08)*. ILO.
