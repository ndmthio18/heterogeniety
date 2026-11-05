# G-real salt-transport analysis

Status: **complete scalar/profile analysis; selected 3-D field rendering remains separate**.

The accepted analysis will separate liquid concentration, dissolved inventory, solid inventory and total salt. F36 will be evaluated over 3--12, 12--28, 28--37 and 3--37 mm, including downward/upward velocity statistics and depth gradients. W3 evaluation includes surface/deep enrichment and precipitation. Gross inward/outward reservoir-filter, filter-sand and F36/W3 advective/diffusive exchange will be reported separately from net exchange.

MRI values retain nominal acquisition times and no smoothing. The known 84--96 h discontinuity and timing/calibration uncertainty will be stated. MRI-visible dissolved Na concentration cannot validate simulated total dissolved-plus-solid inventory.

## Main results

At 174 h, liquid-volume-weighted F36 core (3--37 mm) concentration was
2.2796 M for Greal-75 and 2.2358 M for Greal-81. The corresponding terminal
F36 MRI profile RMSE values were 0.2558 and 0.2912 M. Thus Greal-75 improves
F36 concentration modestly, but this improvement accompanies excessive total
evaporation. Terminal W3 core concentrations were 2.4954 and 2.4883 M, with
terminal MRI RMSE 0.2681 and 0.2602 M; Greal-81 is slightly better for W3.

Greal-75 first exceeded `1e-12 mol` solid salt at 61.083 h and ended with
0.4723 g NaCl-equivalent solid. Greal-81 onset was 71.917 h and terminal solid
was 0.3207 g. In both cases essentially all equilibrium solid inventory was in
W3. These are model equilibrium events, not experimental nucleation times or
visible-crust predictions.

F36/W3/filter salt increments were respectively 0.020283/0.030669/0.003396 mol
for Greal-75 and 0.019602/0.027946/0.003305 mol for Greal-81. Integrated net
F36-to-W3 exchange was 0.027176 mol for Greal-75 and 0.024835 mol for
Greal-81. Gross exchange is substantially larger than net exchange and is
retained in `results/comparison/final_metrics.json`.

The fixed-porosity/permeability formulation gives maximum equivalent solid
volume fractions of 10.60 and 8.29, far above geometric pore capacity. Solid
salt therefore remains a conservation inventory diagnostic; the runs do not
validate crystal morphology, clogging, or external efflorescence.
