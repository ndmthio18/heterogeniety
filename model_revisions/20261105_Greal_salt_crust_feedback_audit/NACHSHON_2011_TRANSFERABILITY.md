# Nachshon 2011 Table 2: verification and G-real transferability

Task 6 / Task 1 only; reviewed 2026-11-05. No solver, parameter or accepted-result changes. The CSV name `VERIFIED` denotes verified transcription, **not successful arithmetic reproduction or physical validation**.

## Primary evidence and access boundary

[Publisher article](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011WR010776), including the publisher's indexed Table 2 at the [alternate DOI route](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2011wr010776), was cross-checked against [parsed original-paper PDF text](https://citeseerx.ist.psu.edu/document?doi=36f33c1955efc77b340d6ad6a25cac201771f318&repid=rep1&type=pdf). Equation 9 is on PDF page 8/16 and Table 2 on page 9/16. Direct publisher access was intermittent; the supplement `wrcr13196-sup-0002-t02.txt` and PDF page-image requests failed. This is text-based cross-verification, not visual PDF verification. No source PDF is redistributed.

## Published values versus independent arithmetic

All rows use reported Delta C_s = 0.015 kg/m³. J below uses dimensionally consistent kg m⁻² s⁻¹; the source header prints `Kg s−1 m²` (positive area exponent). The original header is retained in the CSV. L is in metres; both D columns are in m²/s. H/L retain the source terminology. Source: Table 2, section 4.2, paragraphs 35–36.

| Sand / PE | J | L_salt | Published D_s | J L / Delta C_s | Difference / published |
|---|---:|---:|---:|---:|---:|
| Homo-Fine H | 3.47e-5 | 9.79e-4 | 1.16e-6 | 2.264753e-6 | +95.237% |
| Homo-Fine L | 1.74e-5 | 1.65e-3 | 1.74e-6 | 1.914000e-6 | +10.000% |
| Hetero Fine 1 H | 4.63e-5 | 4.89e-4 | 2.16e-6 | 1.509380e-6 | −30.121% |
| Hetero Fine 1 L | 3.47e-5 | 1.16e-3 | 2.55e-6 | 2.683467e-6 | +5.234% |
| Hetero Fine 2 H | 5.79e-5 | 9.17e-4 | 2.31e-6 | 3.539620e-6 | +53.230% |
| Hetero Fine 2 L | 4.63e-5 | 1.71e-3 | 6.17e-6 | 5.278200e-6 | −14.454% |

Equation 9 is verified: signed Fick form J = −D_s Delta C_s / Delta L_salt; positive magnitudes give D_s = |J| L_salt / |Delta C_s|. Dimensions yield m²/s. No extra porosity or tortuosity multiplier appears in this inversion.

Our Decimal recomputation shows six inconsistencies. Even allowing half a last displayed digit in each input and the published D_s, the resulting intervals do not overlap. These are rounding bounds, **not experimental uncertainty estimates**. The discrepancies have different signs and factors; a single unit conversion cannot reconcile them. Their cause remains unresolved: original unrounded data, calculation worksheets or author clarification are needed. We do not silently replace the published values with our recomputation or claim to have established a corrigendum.

Using the paper's D_air = 2.6695e-5 m²/s at 25°C (paragraph 36), the four **published heterogeneous** ratios are 0.080914, 0.095524, 0.086533 and 0.231129 in table order. Recomputed ratios are also retained in the CSV. Homogeneous values are kept separate.

## Experimental evidence versus assumptions

| Item | Source finding and epistemic status | Location |
|---|---|---|
| Supply / concentration | Constant-head Marriott supply; initially 25 wt% NaCl | Methods, paragraphs 25–27 |
| PE | H 3.84; L 2.4 cm/day, open-water reference, wind controlled | Methods, paragraph 28 |
| Humidity / vapor gradient | Assumed RH 50%, subcrust vapor 0.03 kg/m³ | Section 4.2, paragraph 35 |
| Temperature | 25°C labels D_air, not a verified atmospheric setpoint; ambient T independently measured | Paragraphs 19,36 |
| Local flux | IRT temperature converted through energy balance, checked against weighing; not direct vapor sampling | Section 2.2; paragraph 26 |
| Thickness | Estimated by Eq. 5, not direct geometric measurement | Section 2.2, Eq. 5; paragraph 35 |
| Inversion stage | SS3, assuming slowly growing crust | Paragraph 35 |
| Evaporation plane | Dry-crust/subcrust evaporation assumption for IRT; does not establish every layer always dry | Paragraph 42; Figure 9 |

Equation 5 (PDF page 4/16) expresses thickness growth as Delta L_salt(t) = c integral_0^t e_0(t') dt', with e_0 related to the surface energy balance. Thus inferred thickness and local flux share thermal/evaporation information. D_s is an **effective inverse estimate**, not an independently measured intrinsic transport property. Morphology and the adopted gradient/thickness definitions affect its interpretation.

## Decision for G-real

The target conditions below are the task's specified G-real conditions, not claims attributed to Nachshon.

| G-real condition | Transfer assessment (our inference) |
|---|---|
| Continuous P3 wicking | Sustained supply is a relevant analogy. It does not establish liquid continuity through an external salt crust or the same hydraulic resistance. |
| Initial 1 mol/L NaCl | Cannot inherit the near-saturation/constant-osmotic-potential approximation. Evolving water activity remains necessary. |
| Dry nitrogen, RH approximately 0 | Do not reuse Delta C_s = 0.015 kg/m³. Define vapor concentrations from actual local temperature, water activity and ambient conditions. |
| Nonisothermal coupled transport | The source's 25°C reference ratio is not a temperature law. Retain energy conservation and latent heat; establish thermal and vapor properties separately. |
| W3 efflorescence | Surface coverage, thickness, wetness and contact may vary. Bulk solid inventory is not measured external crust geometry. |
| Existing 8.100162 mm effective air film | Eq. 9 uses subcrust-to-ambient concentration without an explicit external-film subtraction. Consequently, adding its apparent resistance to our calibrated film could double count some resistance; this is an identifiability concern, not a proven error in the paper. |

**What is supported?** The six published values are attributable to these experiments; their exact numerical reconstruction is not supported by the displayed inputs. The heterogeneous reported range 2.16e-6–6.17e-6 m²/s is neither a confidence interval nor a universal G-real bound.

**Can they inform a hypothetical screening?** Yes, as explicitly conditional literature-reported scenarios, paired with the arithmetic discrepancy and alternative recomputed scenarios. They are not defensible as uniquely validated inputs. No screening was executed in this task, and the previous task's figures remain unchanged.

**Before coupling:** obtain the original inversion data and averaging/area conventions; independently constrain crust coverage, external thickness and wet/dry contact; define concentrations at both crust faces and distinguish external-film resistance; constrain thermal conductivity, vapor transport versus temperature/saturation, and liquid connectivity. Use these to formulate identifiable water/salt/energy balances. Neither MRI fitting nor another arbitrary porosity correction resolves the present source inconsistency.

## Reproduction and stop point

Run `python -X utf8 scripts/verify_nachshon_table2.py` from this directory. It writes the six-row CSV, computes all ratios and rounding intervals, and checks the six-row mismatch conclusion. This completes the literature-only Task 1. Task 2 and simulations await review.
