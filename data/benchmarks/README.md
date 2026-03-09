# Benchmark Scales for MAPIG Evaluation

This directory contains 5 published assessment scales used as gold standards for evaluating MAPIG-generated items.

## Selection Criteria

1. **High citation count** - Widely used in research
2. **Open access / public domain** - No restrictive copyright
3. **Established validity** - Documented psychometric properties

## Scales

### 1. IPIP-NEO-60 (Personality)
- **Author:** Goldberg et al. (1999)
- **Domain:** Big Five personality (Extraversion, Agreeableness, Conscientiousness, Neuroticism, Openness)
- **License:** Public Domain
- **Items:** 5 Extraversion items included

### 2. PHQ-9 (Clinical)
- **Author:** Kroenke, Spitzer, & Williams (2001)
- **Domain:** Depression severity
- **License:** Public Domain (Pfizer made available in 2005)
- **Items:** 5 of 9 depression symptom items

### 3. Social Connectedness Scale-Revised (Social)
- **Author:** Lee & Robbins (1995)
- **Domain:** Social belongingness
- **License:** Research use with citation
- **Items:** 5 connectedness items (reverse-scored in original)

### 4. Job Satisfaction Survey (JSS) (Organizational)
- **Author:** Spector (1985)
- **Domain:** Job satisfaction across 9 facets
- **License:** Free for research (per author website)
- **Items:** 5 items across pay, promotion, supervision facets

### 5. Attitude Toward the Environment Scale (Attitudes)
- **Author:** Milfont & Duckitt (2010)
- **Domain:** Environmental attitudes
- **License:** Research use with citation
- **Items:** 5 items measuring environmental concern

## Usage

Load scales in evaluation suite:
```python
from backend.evaluation.benchmark_loader import load_benchmark_scales

scales = load_benchmark_scales()  # Returns list[BenchmarkScale]
```

## Total Test Cases

5 scales × 5 items each = **25 comparison test cases**

Estimated evaluation runtime: 2-5 minutes (LLM-as-judge comparison for 25 items)
