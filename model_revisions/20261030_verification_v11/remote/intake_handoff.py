"""Copy A's immutable handoff snapshot into the v11 tree and verify every hash (Opus B).

Reads A's HANDOFF_READY.json (read-only), copies the snapshot tar into
ROOT/handoff/<version>/, verifies the tar SHA256, extracts it there (never into
A's tree), and checks binary, source, test, mesh and input hashes against the
handoff record. Writes ROOT/handoff/<version>/intake.json. Never modifies A.
Usage: intake_handoff.py [PATH_TO_HANDOFF_READY.json]
"""
from pathlib import Path
import datetime, hashlib, json, shutil, sys, tarfile

ROOT = Path(__file__).resolve().parent.parent
A = Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_causal_v10')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def main(hp):
    hp = Path(hp)
    h = json.loads(hp.read_text())
    ver = h['version']
    dst = ROOT / 'handoff' / ver
    if dst.exists():
        raise SystemExit(f'{dst} exists; intake is immutable (new handoff version needs a new directory)')
    dst.mkdir(parents=True)
    shutil.copy2(hp, dst / 'HANDOFF_READY.json')
    tar_src = Path(h['snapshot_tar'])
    tar = dst / tar_src.name
    shutil.copy2(tar_src, tar)
    res = {'version': ver, 'intake_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
           'handoff_sha256': sha(hp), 'snapshot_sha256': sha(tar), 'snapshot_expected': h['snapshot_tar_sha256'], 'mismatches': []}
    if res['snapshot_sha256'] != h['snapshot_tar_sha256']:
        res['mismatches'].append('snapshot_tar')
    ex = dst / 'snapshot'
    with tarfile.open(tar) as t:
        for m in t.getmembers():
            assert not m.name.startswith('/') and '..' not in Path(m.name).parts, m.name
        t.extractall(ex)
    tag = ver.split('_')[-1]
    exe = ex / f'build_{tag}' / Path(h['binary']).name
    res['binary'] = str(exe)
    res['binary_sha256'] = sha(exe)
    if res['binary_sha256'] != h['binary_sha256']:
        res['mismatches'].append('binary')
    for key, base in [('source_sha256', ex), ('tests_sha256', ex)]:
        for rel, v in (h.get(key) or {}).items():
            p = base / rel
            if not p.exists() or sha(p) != v:
                res['mismatches'].append(f'{key}:{rel}')
    if sha(ex / 'inputs' / 'cylinder.msh') != h['mesh_sha256']:
        res['mismatches'].append('mesh')
    for name, v in h['inputs_sha256'].items():
        if sha(ex / 'inputs' / name) != v:
            res['mismatches'].append(f'input:{name}')
    # the frozen v08 mesh used by v11 medium cases must be the handoff mesh
    v11_medium = ROOT / 'inputs' / 'mesh' / 'cyl_medium_r12t64z40_v08.msh'
    res['v11_medium_mesh_equals_handoff_mesh'] = sha(v11_medium) == h['mesh_sha256']
    if not res['v11_medium_mesh_equals_handoff_mesh']:
        res['mismatches'].append('v11_medium_mesh')
    res['status'] = 'verified' if not res['mismatches'] else 'mismatch'
    (dst / 'intake.json').write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else A / 'HANDOFF_READY.json')
