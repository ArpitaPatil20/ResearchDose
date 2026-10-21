# ResearchDose — Scientific Methodology & Conversion Principles

## 1. Principles of Interspecies Dose Scaling

### Why Direct mg/kg Scaling Fails Across Species
Metabolic rate, cardiac output, renal filtration, and physiological clearance do not scale linearly with body mass ($W^{1.0}$). Instead, in accordance with **Kleiber's Law** and biological allometry, basal metabolic rate scales approximately with body surface area or mass to the $3/4$ power ($W^{0.67} - W^{0.75}$).

Small animals (such as mice) have a much higher surface-area-to-body-mass ratio and markedly faster basal metabolic clearance than larger species (such as dogs and humans). Administering the same nominal mg/kg dose from a mouse directly to a human would result in substantial systemic drug accumulation and potentially life-threatening overdose.

### Body Surface Area (BSA) / $K_m$ Normalization
To normalize for these physiological differences, the standard regulatory approach established in FDA CDER (2005) guidance utilizes the $K_m$ factor:

$$K_m = \frac{\text{Body Weight (kg)}}{\text{Body Surface Area (m}^2\text{)}}$$

The equivalent dose in the target species is computed as:

$$\text{Dose}_{\text{target}} (\text{mg/kg}) = \text{Dose}_{\text{source}} (\text{mg/kg}) \times \frac{K_m(\text{source})}{K_m(\text{target})}$$

### Total Administered Dose
Dose per unit weight is normalized, but total drug mass administered depends on subject weight:

$$\text{Total Dose (mg)} = \text{Dose}_{\text{target}} (\text{mg/kg}) \times \text{Weight}_{\text{target}} (\text{kg})$$

### Formulation Volume
If the therapeutic agent has an active concentration in liquid formulation:

$$\text{Volume (mL)} = \frac{\text{Total Dose (mg)}}{\text{Concentration (mg/mL)}}$$

> **Important**: Physical volume computation is purely arithmetic. Dosing volume limits (e.g., maximum permissible oral gavage or intravenous bolus volumes according to NC3Rs laboratory standards) must be respected by researchers.

---

## 2. Table of Verified Species $K_m$ Factors
*(Source: U.S. FDA CDER Guidance for Industry, July 2005, Table 1; Reagan-Shaw et al., FASEB J 2008)*

| Species | Standard Weight | Body Surface Area (BSA) | $K_m$ Factor | Primary Citation |
|---|---|---|---|---|
| **Human (Adult)** | 60.0 kg | 1.62 m² | **37** | FDA 2005 Table 1 |
| **Mouse** | 0.02 kg (20 g) | 0.007 m² | **3** | FDA 2005 Table 1 |
| **Hamster** | 0.08 kg (80 g) | 0.02 m² | **5** | FDA 2005 Table 1 |
| **Rat** | 0.15 kg (150 g) | 0.025 m² | **6** | FDA 2005 Table 1 |
| **Ferret** | 0.30 kg (300 g) | 0.043 m² | **7** | FDA 2005 Table 1 |
| **Guinea Pig** | 0.40 kg (400 g) | 0.05 m² | **8** | FDA 2005 Table 1 |
| **Rabbit** | 1.80 kg | 0.15 m² | **12** | FDA 2005 Table 1 |
| **Dog (Beagle)** | 10.0 kg | 0.50 m² | **20** | FDA 2005 Table 1 |
| **Monkey (Cynomolgus)** | 2.40 kg | 0.20 m² | **12** | FDA 2005 Table 1 |
| **Monkey (Rhesus)** | 3.20 kg | 0.25 m² | **12** | FDA 2005 Table 1 |
| **Monkey (Marmoset)** | 0.35 kg (350 g) | 0.06 m² | **6** | FDA 2005 Table 1 |
| **Miniature Swine** | 20.0 kg | 0.74 m² | **27** | FDA 2005 Table 1 |
| **Micro-pig** | 8.0 kg | 0.38 m² | **21** | FDA 2005 Table 1 |

---

## 3. Scientific Limitations & Boundaries
BSA scaling is an empirical allometric approximation. It is **NOT** universally suitable in all situations:
1. **Biologics & Monoclonal Antibodies**: Large molecular weight proteins, cytokines, and mAbs clear via neonatal Fc receptor (FcRn) recycling and target-mediated drug disposition (TMDD), where BSA scaling fails.
2. **Species-Specific Metabolism**: Differences in cytochrome P450 isoenzymes (e.g., CYP3A, CYP2D6) or glucuronidation pathways (e.g., cats deficient in UDP-glucuronosyltransferase) require physiologically-based pharmacokinetic (PBPK) modeling.
3. **Safety Starting Dose (MRSD)**: Conversion of an animal NOAEL to Human Equivalent Dose (HED) is only the first step. FDA guidance requires dividing the HED by a minimum safety factor (typically 10-fold or higher) to calculate the Maximum Recommended Starting Dose.
