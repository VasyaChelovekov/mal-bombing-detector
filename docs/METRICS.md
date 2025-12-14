# Detection Metrics Documentation

This document provides detailed technical documentation for the review bombing detection metrics used in the MAL Review Bombing Analyzer.

## Overview

The detection system uses a multi-factor statistical approach that combines several complementary metrics. Each metric captures a different aspect of potential vote manipulation, and the final suspicion score is a weighted combination of all components.

## Primary Metrics

### 1. Ones Z-Score

**Purpose**: Measure how statistically unusual the number of 1-votes is compared to what would be expected for a given MAL score.

**Calculation**:
```
z = (observed_ones_percent - expected_ones_percent) / std_dev
```

Where:
- `observed_ones_percent` = Actual percentage of 1-votes
- `expected_ones_percent` = Expected percentage based on MAL score (from reference distribution)
- `std_dev` = Standard deviation from population data

**Interpretation**:
- Z > 3.0: Highly anomalous (beyond 99.7th percentile)
- Z > 2.0: Significantly unusual (beyond 95th percentile)
- Z < 1.0: Within normal variation

**Weight**: 25%

### 2. Spike Ratio

**Purpose**: Detect isolated spikes in the distribution, particularly at score 1.

**Calculation**:
```
spike_ratio = votes[1] / mean(votes[2:4])
```

This compares the 1-votes to the average of scores 2-4 (the immediate neighbors).

**Interpretation**:
- Ratio > 5.0: Clear spike, strong indicator
- Ratio > 3.0: Suspicious spike
- Ratio < 2.0: Normal distribution shape

**Weight**: 20%

### 3. Distribution Effect Size (Cohen's d)

**Purpose**: Quantify the overall difference between the observed distribution and what would be expected for a healthy anime of that rating.

**Calculation**:
```
d = (mean_observed - mean_expected) / pooled_std_dev
```

Applied across the entire 10-point distribution.

**Interpretation**:
- d > 0.8: Large effect (substantial manipulation)
- d > 0.5: Medium effect
- d < 0.2: Small effect (minimal deviation)

**Weight**: 20%

### 4. Entropy Deficit

**Purpose**: Measure how much the distribution deviates from maximum entropy (information-theoretic approach).

**Calculation**:
```
max_entropy = log2(10)  # Maximum for 10 categories
actual_entropy = -Σ p(i) * log2(p(i))
deficit = (max_entropy - actual_entropy) / max_entropy
```

**Interpretation**:
- High deficit: Distribution is concentrated (potential manipulation)
- Low deficit: Distribution is spread out (natural voting)

**Weight**: 15%

### 5. Bimodality Index

**Purpose**: Detect polarization where votes concentrate at both extremes (1 and 10).

**Calculation**:
Based on Ashman's D coefficient:
```
bimodality = f(skewness, kurtosis, sample_size)
```

Also considers the raw percentage of extreme votes:
```
polarization = (ones_percent + tens_percent) / 100
```

**Interpretation**:
- Index > 0.7: Strong bimodality (controversy or manipulation)
- Index > 0.5: Moderate bimodality
- Index < 0.3: Unimodal (normal)

**Weight**: 10%

### 6. Contextual Factors

**Purpose**: Adjust scores based on anime-specific context.

**Components**:
- **Member count adjustment**: Lower confidence for low-member anime
- **Vote count reliability**: Minimum threshold for statistical validity
- **Age factor**: Older anime may have more natural variation

**Weight**: 10%

## Composite Suspicion Score

The final suspicion score is calculated as:

```python
suspicion_score = Σ (weight[i] * component_score[i])
```

Where each component score is normalized to [0, 1] range before weighting.

### Normalization Functions

Each raw metric is converted to a [0, 1] score using sigmoid or threshold functions:

```python
# Z-score normalization
score = 1 / (1 + exp(-k * (z - threshold)))

# Ratio normalization  
score = min(1.0, (ratio - 1) / (max_ratio - 1))

# Effect size normalization
score = min(1.0, effect_size / max_effect_size)
```

## Severity Classification

| Level | Score Range | Criteria |
|-------|-------------|----------|
| **Critical** | ≥ 0.80 | Multiple strong indicators, high confidence |
| **High** | 0.65-0.79 | Clear anomalies in 2+ metrics |
| **Moderate** | 0.50-0.64 | Suspicious patterns detected |
| **Low** | 0.35-0.49 | Minor anomalies |
| **Minimal** | 0.20-0.34 | Within expected variation |
| **None** | < 0.20 | No evidence of manipulation |

## Reliability Indicators

### Is Reliable Flag

Results are marked as unreliable when:
- Total votes < 1,000
- Members < 10,000
- Significant data parsing issues

### Confidence Score

A secondary confidence score (0-1) indicates how trustworthy the suspicion score is:
- High confidence: Large sample size, clear patterns
- Low confidence: Small sample, ambiguous signals

## Expected Distribution Model

For comparison, we generate expected distributions based on the anime's MAL score:

```python
def generate_expected_distribution(mal_score: float) -> list[float]:
    """
    Generate expected vote distribution for a given MAL score.
    
    Based on empirical analysis of non-bombed anime distributions.
    Uses a shifted beta distribution centered on the MAL score.
    """
    # Center of distribution (mapped to 1-10 scale)
    center = mal_score
    
    # Spread depends on score (higher scores have tighter distributions)
    spread = 1.5 - (mal_score - 5) * 0.05
    
    # Generate beta distribution
    alpha = center / spread
    beta = (10 - center) / spread
    
    # Sample and normalize
    ...
```

## Validation

The algorithm has been validated against:

1. **Known bombing cases**: Anime with documented brigading incidents
2. **Control group**: Highly-rated anime with no controversy
3. **Edge cases**: New releases, niche anime, sequels

### False Positive Rate

In validation testing:
- False positive rate: ~5% at "Moderate" threshold
- False positive rate: ~1% at "High" threshold
- False positive rate: <0.1% at "Critical" threshold

### Limitations

1. Cannot distinguish between organized bombing and genuine controversy
2. May flag anime with legitimately divisive content
3. Historical patterns may differ from current trends
4. Platform-specific factors not fully accounted for

## References

1. Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences
2. Ashman, K. M. et al. (1994). Detecting bimodality in astronomical datasets
3. Shannon, C. E. (1948). A Mathematical Theory of Communication
