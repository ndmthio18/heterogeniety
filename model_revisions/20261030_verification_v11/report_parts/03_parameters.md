## 6. Parameter-uncertainty review

Source: `experimental_data/DARUS-6478/.../F36 & W3 Sand Hydraulic Properties.xlsx` (SHA256 d63221c0…, read with formulas; dump `analysis/hydraulic_workbook_dump.txt`).

| quantity | replicate record | model value | traceable interval used |
|---|---|---|---|
| Ks F36 | 3 packings × 3 repeats: 658/669/669, 681/675/656, 624/640/645 cm/d (7.3–7.9e-5 m/s); packing means 7.77/7.77/7.40e-5 m/s | k=7.819e-12 m² (= mean 7.644e-5 m/s via k=Ks·μ/(ρg), μ=1.002e-3, ρ=998, g=9.81, the workbook's own conversion) | 7.3–7.9e-5 m/s (−4.5 %/+3.3 %) |
| Ks W3 | 3 packings: 2.6/2.7/2.7, 2.7/2.7/2.7, 2.7/2.7 cm/d; m/s sheet 3.0–3.2e-7; sheet means use the first 2 repeats | k=3.2034e-14 m² (= 3.133e-7 m/s) | 3.0–3.2e-7 m/s (−4.3 %/+2.1 %) |
| porosity F36 | Table 2 (250 mL): 0.3939/0.3989/0.3897; oven drying (100 cm³): 0.3980/0.3970/0.3992 | 0.40 | model value lies above every replicate |
| porosity W3 | 0.3483/0.3632/0.3494; 0.3471/0.3572/0.3637 | 0.36 | 0.347–0.364 |
| Brooks–Corey pe, λ, Swr | single least-squares fits per sand to pooled replicate curves; no reported interval | as fitted | none (refitting would be a new fit) |
| D0, tortuosity, D_eff, dispersion | no independent record | inherited laws | none |

Limits: the replicates are separate laboratory packings (cylinders 5 cm × 8 cm; 100 cm³ rings), not the MRI column. Their spread is a lower bound on the column's parameter uncertainty; packing differences between test cylinders and the experiment column are unquantified. No retention-curve or diffusion interval exists, so no statement can be made that any effect exceeds the parameter uncertainty as a whole.
