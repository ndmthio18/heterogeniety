# Preparation / repair record

2026-11-02: local preparation initially stopped at an ambiguous replacement anchor occurring twice in the upstream-derived volumevariables file. No source had been modified and no compiler/solver launched. Verified the staging source hashes still matched the parent, then narrowed the intended first/update occurrence while asserting the expected count. No existing revision or run changed.

All future build/gate/solver failures must be appended here with preserved logs; no hidden physics, parameter, tolerance or retry-cap changes.

## Validation log parser repair, 2026-11-02
Both Precipitate_dt30/dt15 solver exits were0 at600s. The controller incorrectly expected FIXED_HYDRAULICS enabled=1, but inherited stream boolalpha prints enabled=true. Traceback identified this sole early assertion. Original controller, statuses, logs and manifests retained in provenance/validation_attempt01; raw untouched. Parser corrected; successful solver results revalidated without reruns. No binary, input, physics or tolerance changes. Explicit --resume-validation-repair accepts only prior returncode0 and unchanged input/binary; numerical failures cannot be resumed this way.

## Local monitor exit, 2026-11-02 17:30 UTC
Local PID59840 no longer exists; no other python.exe with this revision/sonnet_monitor.py command line exists. Last monitor record16:49 UTC showed healthy production and747/748 SHA-verified files. stdout/stderr empty; no monitor_error or terminal notification. Exit cause cannot be established from available logs. Remote controller2580724 and solver2583239 remain alive and advance normally. Preserved old lock/status/logs in provenance/monitor_exit_20261102_1730UTC before restarting only the local monitor; no solver or physical/numerical setting changed.

## Local monitor exit, 2026-11-02 23:40 UTC
PID39672 absent and no matching monitor process. Last status21:34 UTC, stdout/stderr empty, no terminal record. Exit cause remains unknown. Preserved lock/status/logs in provenance/monitor_exit_20261102_2340UTC; restarted only local backup monitor as PID43740. Controller2580724 and solver2583239 alive; production accepted171.5833h with maxrelativebudgeterror2.81e-12. No solver, physics, tolerance or fitting changes.
