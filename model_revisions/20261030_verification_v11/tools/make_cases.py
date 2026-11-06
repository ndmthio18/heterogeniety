"""Generate v11 production inputs/specs/queue from a verified A handoff (Opus B).

Run locally after the remote intake has verified the snapshot and its
inputs were copied to handoff/<version>/snapshot/inputs/ locally.
Usage: python make_cases.py VERSION [--with-b0] [--with-params]
Writes inputs/prod_<VERSION>/*.input (+ .diff.json), specs/prod_<VERSION>/*.json and
specs/prod_<VERSION>/queue.json (registered priority order of DESIGN.md).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_inputs

ROOT = Path(__file__).resolve().parent.parent
R = '/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11'
MESH = {'coarse': ('cyl_coarse_r8t48z27.msh', '1.0028615075117908'),
        'medium': ('cyl_medium_r12t64z40_v08.msh', None),
        'fine': ('cyl_fine_r18t96z60.msh', '1.0007143040431583')}
KS2K = 1.002e-3 / (998 * 9.81)  # workbook conversion Ks (m/s) -> k (m2)

# (case id, mesh, changes) in the registered order; each expanded to C1 and C0 arms
BASE = [
    ('G_coarse', 'coarse', {}),
    ('T150', 'medium', {('TimeLoop', 'MaxTimeStepSize'): '150'}),
    ('G_fine', 'fine', {}),
    ('S2', 'medium', {('Revision', 'RandomSeed'): '2'}),
    ('S3', 'medium', {('Revision', 'RandomSeed'): '3'}),
    ('A3e-6', 'medium', {('Revision', 'PerturbationStd'): '3e-06'}),
    ('A3e-5', 'medium', {('Revision', 'PerturbationStd'): '3e-05'}),
]
PARAMS = [
    ('P1', 'medium', {('SpatialParams', 'CoarsePermeability'): repr(7.3e-5 * KS2K), ('SpatialParams', 'FinePermeability'): repr(3.2e-7 * KS2K)}),
    ('P2', 'medium', {('SpatialParams', 'CoarsePermeability'): repr(7.9e-5 * KS2K), ('SpatialParams', 'FinePermeability'): repr(3.0e-7 * KS2K)}),
]
B0 = [('G_fine', 'fine', {}), ('T150', 'medium', {('TimeLoop', 'MaxTimeStepSize'): '150'})]


def main(ver, with_b0=False, with_params=False):
    tdir = ROOT / 'handoff' / ver / 'snapshot' / 'inputs'
    idir = ROOT / 'inputs' / f'prod_{ver}'
    sdir = ROOT / 'specs' / f'prod_{ver}'
    idir.mkdir(parents=True, exist_ok=True)
    sdir.mkdir(parents=True, exist_ok=True)
    intake = json.loads((ROOT / 'handoff' / ver / 'intake.json').read_text())
    assert intake['status'] == 'verified'
    binary_remote = intake['binary']
    queue = []
    plan = [(c, m, ch, 'B1') for c, m, ch in BASE]
    if with_params:
        plan += [(c, m, ch, 'B1') for c, m, ch in PARAMS]
    if with_b0:
        plan += [(c, m, ch, 'B0') for c, m, ch in B0]
    for cid, mesh, ch, b in plan:
        for arm in ('C1', 'C0'):
            name = f'v11_{cid}_{arm}{b}'
            template = tdir / f'{arm}{b}_24h.input'
            changes = dict(ch)
            mfile, corr = MESH[mesh]
            changes[('Grid', 'File')] = mfile
            if corr:
                changes[('Revision', 'WaterFluxAreaCorrection')] = corr
            if not (idir / f'{name}.input').exists():
                make_inputs.derive(template, idir, name, changes)
            fine = mesh == 'fine'
            spec = {'name': name, 'case_id': cid, 'arm': arm + b, 'mesh_level': mesh,
                    'input': f'{R}/inputs/prod_{ver}/{name}.input', 'mesh': f'{R}/inputs/mesh/{mfile}',
                    'binary': binary_remote, 'binary_sha256': intake['binary_sha256'], 'handoff_version': ver,
                    'wall_s': (12 if fine else 6) * 3600, 'cpu': 5,
                    'extra_files': [f'{R}/handoff/{ver}/snapshot/inputs/water_flux_zero_storage.txt',
                                    f'{R}/handoff/{ver}/snapshot/inputs/forcing_provenance.json'],
                    'expected_scratch_GiB': 2.0 if fine else 1.0, 'min_mem_GiB': 8.0, 'extract': True}
            p = sdir / f'{name}.json'
            p.write_text(json.dumps(spec, indent=1))
            queue.append(f'{R}/specs/prod_{ver}/{name}.json')
    (sdir / 'queue.json').write_text(json.dumps(queue, indent=1))
    print(json.dumps(queue, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], '--with-b0' in sys.argv, '--with-params' in sys.argv)
