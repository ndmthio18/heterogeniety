# sal 7–8 mm nonisothermal film calibration

User authorized calibration in 7–8 mm on sal with multiple cores. Run independent Film075mm (7.5 mm) and Film080mm (8.0 mm), each 2 h pre-equilibration plus 174 h evaporation. Existing accepted Frodo Film07mm supplies the 7.0 mm endpoint (58.992496504 g, +14.504069%). Old user-stopped cases remain stopped.

RH=0, fixed porosity and permeability, 20 C initial/ambient/reservoir; unchanged phase equilibrium, precipitation, thermal closure, grid, 300 s timestep ceiling, tolerances and outputs. FilmThickness is the only fitted parameter, including its existing coupling to mass/heat transfer. No renormalization to measured mass and no clock shift.

Primary target: measured reservoir SOLUTION loss over 1–174 h = 51.52 g; numerical fit tolerance 1%. Compare duration-weighted interval-rate RMSE over all measured intervals. Accept full endpoint and water/salt/energy/complementarity budgets before fitting. Short curves cannot establish a full-window bracket. If an accepted sign-changing interval exists, permit one bounded secant candidate within 7–8 mm; review further work if no bracket or candidate misses tolerance. Never enlarge the interval silently.

Slurm debug partition, one task with four physical cores per case, DUMUX_NUM_THREADS=4, OMP/BLAS=1, nice10, 48 h/case and 4 GiB free-space reserve. Other projects and liqin runs unchanged. Home quota full; isolated writable /tmp is used and final raw must be transferred and hash-verified locally before cleanup. Slurm reports RealMemory=1 MB despite physical free memory >200 GiB, so explicit memory request cannot be scheduled; no memory allocation override is attempted.

Frozen Frodo compiled ELF SHA256 9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5 is used with exact bundled libraries/OpenMPI plugins. Loader and library path relocation changes ELF hash but no compiled code. Build manifest records both and all runtime hashes. Native sal binaries must not load bundled glibc. Only solver rank-discovery environment is cleared to allow single-process MPI initialization; Slurm allocation and controller tracking remain active.

Before production: six reaction tests, injected-recovery test and original-grid equilibrium regression; recovery must hit real invalid trial and timestep retry, reaction timestep endpoints must agree, original-grid budgets/temperature endpoint agree with frozen Frodo within 1e-7 normalized error. Production jobs depend on successful gate job exit AND explicitly check gates_status passed.

Fitting evaporation does not independently validate physics. Fixed phi/K solid inventory can exceed geometric pore capacity; it is an inventory diagnostic, not physically valid pore occupation or an external efflorescent crust model. No new grid/full-window timestep convergence claimed.
