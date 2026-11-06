"""Derive v11 case inputs from a frozen template, changing only registered keys.

Every derived input records its template SHA256 and exact key diff in
inputs/<name>.diff.json; any change outside ALLOWED aborts.
Usage: python make_inputs.py TEMPLATE OUTDIR NAME key=value [key=value ...]
"""
import configparser, hashlib, json, sys
from pathlib import Path

ALLOWED = {('Problem', 'Name'), ('Grid', 'File'), ('Revision', 'WaterFluxAreaCorrection'),
           ('TimeLoop', 'MaxTimeStepSize'), ('Revision', 'RandomSeed'), ('Revision', 'PerturbationStd'),
           ('TimeLoop', 'TEnd'),
           # parameter screening only (exploratory, labelled as such)
           ('SpatialParams', 'CoarsePermeability'), ('SpatialParams', 'FinePermeability'),
           ('Revision', 'SaltDiffusionScale')}


def load(p):
    c = configparser.ConfigParser()
    c.optionxform = str
    c.read(p)
    return c


def derive(template, outdir, name, changes):
    c = load(template)
    before = {(s, k): v for s in c.sections() for k, v in c[s].items()}
    changes = dict(changes)
    changes[('Problem', 'Name')] = name
    for (s, k), v in changes.items():
        if (s, k) not in ALLOWED:
            raise SystemExit(f'not an allowed v11 change: {s}.{k}')
        if k not in c[s] and (s, k) != ('Problem', 'Name'):
            raise SystemExit(f'key absent from template: {s}.{k}')
        c[s][k] = v
    out = Path(outdir) / f'{name}.input'
    if out.exists():
        raise SystemExit(f'{out} exists; inputs are immutable')
    with open(out, 'w', newline='\n') as f:
        c.write(f)
    after = {(s, k): v for s in c.sections() for k, v in c[s].items()}
    diff = {f'{s}.{k}': [before.get((s, k)), after.get((s, k))] for (s, k) in set(before) | set(after) if before.get((s, k)) != after.get((s, k))}
    rec = {'name': name, 'template': str(template), 'template_sha256': hashlib.sha256(Path(template).read_bytes()).hexdigest(),
           'input_sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'diff': diff}
    (Path(outdir) / f'{name}.diff.json').write_text(json.dumps(rec, indent=1))
    return rec


if __name__ == '__main__':
    t, o, n = sys.argv[1:4]
    ch = {}
    for kv in sys.argv[4:]:
        k, v = kv.split('=', 1)
        s, key = k.split('.', 1)
        ch[(s, key)] = v
    print(json.dumps(derive(t, o, n, ch), indent=1))
