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

## Bombing Score Adjustments (v1.2.0+)

To reduce false positives—particularly on highly-rated, popular anime—the system applies several adjustments before final classification.

### 1. Minimum Ones Percentage Thresholds

High severity levels now require a minimum percentage of 1-votes:

| Level | Score Threshold | Min `ones_percent` | Effect if Below Threshold |
|-------|-----------------|-------------------|---------------------------|
| **Critical** | ≥ 0.75 | ≥ 2.0% | Downgraded to High or Medium |
| **High** | ≥ 0.55 | ≥ 1.5% | Downgraded to Medium |

**Rationale**: Real bombing campaigns generate a substantial spike in 1-votes. Anime with high composite scores but low 1-vote percentages are likely popular titles with concentrated 10-votes, not bombing victims.

**Example**: Frieren (score 0.68, ones_percent 0.99%) → Downgraded from HIGH to MEDIUM.

### 2. Popularity Discount

When an anime exhibits signs of being popular rather than bombed, the effect size is discounted:

**Trigger Conditions**:
- `tens_percent > 45.0%` (high concentration of 10-votes)
- `ones_percent < 1.5%` (low 1-vote count)

**Effect**: `effect_size *= 0.5`

**Rationale**: Popular anime often have unusual distributions due to genuine fan enthusiasm, not manipulation. The discount prevents the effect size metric from inflating the score.

**Configuration**:
```yaml
bombing_score_adjustments:
  popularity_discount:
    enabled: true
    tens_threshold: 45.0    # % of 10-votes to trigger
    ones_threshold: 1.5     # max % of 1-votes
    discount_factor: 0.5    # multiplier applied to effect_size
```

### 3. Spike Damping

The spike ratio contribution is damped when 1-vote percentages are low:

| `ones_percent` | Damping Factor | Effect |
|----------------|----------------|--------|
| ≥ 2.0% | 1.0 | Full weight (no damping) |
| 0.5% – 2.0% | Linear 0.25–1.0 | Proportional reduction |
| < 0.5% | 0.0 | Spike ignored entirely |

**Calculation**:
```python
if ones_pct >= min_ones_for_full_weight:
    damping = 1.0
elif ones_pct < min_ones_to_consider:
    damping = 0.0
else:
    damping = 0.25 + 0.75 * (ones_pct - min_ones_to_consider) / (min_ones_for_full_weight - min_ones_to_consider)

spike_score *= damping
```

**Rationale**: A spike ratio of 5.0 means something very different when ones_percent is 0.5% vs 5%. Small absolute spikes shouldn't disproportionately affect the composite score.

**Configuration**:
```yaml
bombing_score_adjustments:
  spike_damping:
    enabled: true
    min_ones_for_full_weight: 2.0   # ones_pct for full spike weight
    min_ones_to_consider: 0.5       # below this, spike is ignored
```

### Combined Effect

These adjustments work together to create a more objective scoring system:

1. **Popularity Discount** reduces the effect size for popular anime
2. **Spike Damping** reduces the spike contribution when 1-votes are minimal
3. **Min Ones Thresholds** prevent high severity labels without sufficient evidence

This significantly reduces false positives on anime like:
- Frieren (65% tens, 0.99% ones) → Was HIGH, now MEDIUM
- Steins;Gate (58% tens, 0.68% ones) → Was HIGH, now LOW
- FMA: Brotherhood (53% tens, 0.53% ones) → Was CRITICAL, now MEDIUM

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
