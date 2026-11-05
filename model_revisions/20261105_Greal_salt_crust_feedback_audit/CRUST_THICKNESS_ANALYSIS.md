# Equivalent external thickness

NaCl equivalent mass uses 58.44 g/mol. h=M/[rho (1-epsilon) A f], A=pi(0.025 m)^2/2. This analytical half area is 0.0009817477 m²; the discrete half-face area is 0.0009801714 m² (about 0.16% smaller). The requested analytical area is used consistently for height, actual face areas for evaporation.

At 174 h, Greal-81 contains 0.320707 g and Greal-75 0.472274 g solid equivalent. Assigning all top-1-mm inventory externally, with rho=2165 kg/m³ and epsilon=0.43, gives 0.264713 and 0.389817 mm. Full coverage, 75%, 50% and 25% yield heights proportional to 1/f: Greal-81 0.2647, 0.3530, 0.5294, 1.0589 mm; Greal-75 0.3898, 0.5198, 0.7796, 1.5593 mm.

At full coverage, changing porosity from 0.43 to 0.30 or 0.60 multiplies height by 0.57/0.70 or 0.57/0.40. Changing density to the alternative 2650 kg/m³ multiplies it by 2165/2650. This alternative is not measured NaCl density. Complete combinations and finite-difference growth rates are supplied in terminal/hourly CSVs; accepted-step sensitivity histories are reproducible remotely without downloading additional raw fields.

Top-1-mm, top-2-mm and all-W3 assignments agree to numerical noise because solid lies at the top. This does not resolve the unknown external fraction: if only fraction alpha is external, every reported height is multiplied by alpha. Alpha=0 remains possible under the storage definition. Peak full-coverage height-growth rates are 0.004744 and 0.006036 mm/h, respectively; these are postprocessed inventory rates, not observed geometric growth.

Native selected fields locate positive solid in the uppermost 0.0667 mm cells. At 174 h the equivalent solid-volume maximum is 8.2906/10.5976 in Greal-81/75, exceeding pore capacity. Fixed hydraulics permit an inventory representation; they do not resolve a physical crystal geometry. Reassigning the inventory externally is a hypothesis, not a correction to the accepted solver.
