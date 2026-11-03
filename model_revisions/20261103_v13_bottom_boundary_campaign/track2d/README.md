# 2D mechanism track on Frodo

Active deployment: DEPLOYMENT.json. Source physics is the isolated conventional2D adaptation described in ../MODEL_2D_IMPLEMENTATION.md. Frozen ELF and runtime manifests are under build/provenance. The directory build_sal is an adapter name retained from initial staging; the active Frodo manifest explicitly identifies native Frodo execution with no relocation.

supervisor_frodo.py owns an exclusive lock and schedules core acceptance before independent B cases and G acceptance, then G production. At most6 serial processes on physical CPUs4–9,1thread/nice10;48h/case and disk/memory guards. No automatic retry on numerical failure. All original sal2D submissions were held and never started; they were cancelled before this deployment (provenance/sal_unstarted_cancellation.json). Do not run submit.py again or launch both hosts.

controller.py requires actual Slurm or explicit authorized Frodo local mode. All input/source hashes checked before runs. Every case has independent inputs/raw/status/logs. analyze.py reads saved states and native ledgers without restarting a solver. Static probes and targeted numerical screens precede all long runs. Current core is running; do not call174h predictions completed.

Large binaries, raw VTU, build transport and scalar archives stay outside Git. build.py uses the pinned dependency tree; compile manifests document exact commands. prepare_2d.py reconstructs source from the frozen parent and generates meshes/configuration; it refuses to overwrite a locally built revision. Runtime verification must be repeated after any future source change.
