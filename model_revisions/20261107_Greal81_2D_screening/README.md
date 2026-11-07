# Greal-81 Cartesian 2D screening

This isolated revision implements Task 10's mechanism-screening model. It is
derived from `research/greal81-coupling-regime-map` commit `b8fc42c`, whose
physical baseline traces to Greal-81 commit `469b6a9`. It does not modify the
accepted 3D model or the concurrently running Task 9 calculations.

The primary domain is a Cartesian vertical rectangle of width
`pi*25/2 = 39.269908 mm`, split equally into F36 and W3 and extruded by
`50 mm`. This mapping exactly preserves the 3D sand volume, top evaporation
area and direct vertical interface area. Configuration B adds the explicit
4.5 mm P3 filter and an area-equivalent `0.251327 mm` reservoir inlet.
Configuration A is the full-width pressure-controlled supply control.

Current status: source and inputs prepared; HPCC build job `16345621` is the
first live gate. No screening case has been released.

Reproduction:

```text
python -X utf8 scripts/prepare_campaign.py
sbatch slurm/build_hpcc.slurm
python3 scripts/submit_gates.py   # only after build hash/ldd verification
```

Large VTK data and binaries remain under
`/WORK/hulm_work/zhixin/Greal81_2D_screening_20261107`; they are not Git
deliverables.
