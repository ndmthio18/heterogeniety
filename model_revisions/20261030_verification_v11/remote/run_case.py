"""Run one registered v11 case serially on the assigned CPU (Opus B).

Never overwrites: the run directory must not exist. Resource gates are
checked before launch (waiting, not failing, while resources are short).
Closed VTU frames are gzip-archived with raw/decompressed SHA256 equality
before the raw copy (only this run's own new file) is removed.
Usage: run_case.py CASE_JSON
CASE_JSON keys: name, input, mesh, binary, binary_sha256, wall_s, cpu, extra_files
"""
from pathlib import Path
import datetime, gzip, hashlib, json, os, shutil, subprocess, sys, time, configparser

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path('/tmp/zhixin_verification_v11_20261030')
HOME = Path('/home/zhixin')
GiB = 1024 ** 3


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def write(p, d):
    p = Path(p)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(d, indent=1))
    tmp.replace(p)


def mem_available():
    for l in open('/proc/meminfo'):
        if l.startswith('MemAvailable:'):
            return int(l.split()[1]) * 1024
    raise RuntimeError('no MemAvailable')


def resources():
    return {'mem_available_GiB': mem_available() / GiB,
            'scratch_free_GiB': shutil.disk_usage(SCRATCH).free / GiB,
            'home_free_GiB': shutil.disk_usage(HOME).free / GiB,
            'loadavg': open('/proc/loadavg').read().split()[:3]}


def vm_hwm(pid):
    try:
        for l in open(f'/proc/{pid}/status'):
            if l.startswith('VmHWM:'):
                return int(l.split()[1]) * 1024
    except OSError:
        return None


def last_budget(out):
    p = out / 'budget.csv'
    if not p.exists():
        return None
    with open(p, 'rb') as f:
        f.seek(0, 2)
        n = f.tell()
        f.seek(max(0, n - 20000))
        lines = f.read().decode(errors='replace').splitlines()
    head = open(p).readline().strip().split(',')
    for l in reversed(lines):
        v = l.split(',')
        if len(v) == len(head):
            try:
                return dict(zip(head, map(float, v)))
            except ValueError:
                continue
    return None


def compress_closed(out, final=False):
    paths = sorted(out.glob('*.vtu'))
    if not final:
        paths = paths[:-2]
    for p in paths:
        assert p.resolve().is_relative_to(SCRATCH.resolve()) and p.parent == out
        gz = p.with_name(p.name + '.gz')
        assert not gz.exists(), gz
        before = sha(p)
        tmp = Path(str(gz) + '.tmp')
        with p.open('rb') as src, gzip.open(tmp, 'wb', compresslevel=6) as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        h = hashlib.sha256()
        with gzip.open(tmp, 'rb') as src:
            for c in iter(lambda: src.read(1 << 20), b''):
                h.update(c)
        assert h.hexdigest() == before, 'compression changed raw field'
        tmp.replace(gz)
        entry = {'file': gz.name, 'raw_sha256': before, 'gzip_sha256': sha(gz), 'raw_bytes': p.stat().st_size, 'gzip_bytes': gz.stat().st_size}
        with (out / 'compressed_fields.jsonl').open('a') as f:
            f.write(json.dumps(entry) + '\n')
        p.unlink()  # only this run's own frame, after verified reversible archive


def validate(out, cfg):
    import numpy as np
    lines = (out / 'budget.csv').read_text().splitlines()
    head = lines[0].split(',')
    rows = np.array([l.split(',') for l in lines[1:] if len(l.split(',')) == len(head)], dtype=float)
    b = {h: rows[:, i] for i, h in enumerate(head)}
    target = float(cfg['TimeLoop']['TEnd'])
    res = {'final_time_s': float(b['time_s'][-1]), 'target_time_s': target,
           'final_evaporation_h': float(b['evaporation_time_h'][-1]), 'accepted_steps': len(rows) - 1,
           'all_finite': bool(np.isfinite(rows).all()),
           'max_precip_vf': float(b['precip_vf_max'].max()), 'min_S': float(b['S_min'].min()),
           'max_C_mol_L': float(b['C_max_mol_L'].max())}
    rel = {}
    for c, base in [('water_residual_mol', 'water_mol'), ('salt_residual_mol', 'salt_total_mol'),
                    ('coarse_residual_mol', 'coarse_salt_mol'), ('fine_residual_mol', 'fine_salt_mol')]:
        rel[c] = float(np.abs(b[c]).max() / abs(b[base][0]))
    res['max_relative_residuals'] = rel
    ok = (abs(res['final_time_s'] - target) < 1e-6 and res['all_finite'] and res['max_precip_vf'] == 0
          and res['min_S'] > 0 and max(rel.values()) < 1e-6)
    res['status'] = 'passed' if ok else 'failed'
    return res


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    name = spec['name']
    SCRATCH.mkdir(exist_ok=True)
    out = SCRATCH / 'runs' / name
    status_path = ROOT / 'status' / f'{name}.json'
    status_path.parent.mkdir(exist_ok=True)
    meta = {'case': name, 'state': 'waiting_resources', 'spec': spec, 'runner_pid': os.getpid(),
            'runner_sha256': sha(__file__), 'raw_path': str(out), 'created_utc': utc()}
    if out.exists():
        raise SystemExit(f'{out} exists; never overwrite a run identity')
    binary = Path(spec['binary'])
    assert sha(binary) == spec['binary_sha256'], 'binary hash mismatch'
    need_mem = spec.get('min_mem_GiB', 8.0)
    need_scratch = 8.0 + spec.get('expected_scratch_GiB', 2.0)
    while True:
        r = resources()
        meta.update(resources=r, updated_utc=utc())
        if r['mem_available_GiB'] >= need_mem and r['scratch_free_GiB'] >= need_scratch and r['home_free_GiB'] >= 2.0:
            break
        meta['waiting_reason'] = f"need mem>={need_mem} scratch>={need_scratch} home>=2 GiB"
        write(status_path, meta)
        time.sleep(60)
    out.mkdir(parents=True, exist_ok=False)
    inp = Path(spec['input'])
    shutil.copy2(inp, out / inp.name)
    shutil.copy2(spec['mesh'], out / Path(spec['mesh']).name)
    for f in spec.get('extra_files', []):
        shutil.copy2(f, out / Path(f).name)
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(out / inp.name)
    assert cfg['Grid']['File'] == Path(spec['mesh']).name
    meta.update(input_sha256=sha(out / inp.name), mesh_sha256=sha(out / Path(spec['mesh']).name),
                binary_sha256=spec['binary_sha256'], cpu=spec['cpu'], start_utc=utc(), state='running')
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', TBB_NUM_THREADS='1')
    wall = float(spec['wall_s'])
    with (out / 'simulation.log').open('w') as log:
        proc = subprocess.Popen(['taskset', '-c', str(spec['cpu']), 'nice', '-n', '10', str(binary), str(out / inp.name)],
                                cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
        meta['solver_pid'] = proc.pid
        write(out / 'run_manifest.json', meta)
        write(status_path, meta)
        begin = time.monotonic()
        peak = 0
        try:
            while proc.poll() is None:
                time.sleep(20)
                h = vm_hwm(proc.pid)
                peak = max(peak, h or 0)
                lb = last_budget(out)
                r = resources()
                meta.update(peak_rss_GiB=peak / GiB, resources=r, updated_utc=utc(), wall_h=(time.monotonic() - begin) / 3600)
                if lb:
                    meta.update(reached_evaporation_h=lb['evaporation_time_h'], dt_s=lb['dt_s'], S_min=lb['S_min'], C_max_mol_L=lb['C_max_mol_L'])
                write(status_path, meta)
                if time.monotonic() - begin > wall:
                    raise RuntimeError(f'wall-time limit {wall/3600:.1f} h reached')
                if r['scratch_free_GiB'] < 8.0:
                    raise RuntimeError('scratch reserve below 8 GiB')
                if r['mem_available_GiB'] < 1.5:
                    raise RuntimeError('MemAvailable below 1.5 GiB; stopping own solver to protect other processes')
                if spec.get('compress', True):
                    compress_closed(out)
        except Exception as exc:
            meta['failure_reason'] = str(exc)
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        proc.wait()
    meta.update(returncode=proc.returncode, end_utc=utc(), wall_h=(time.monotonic() - begin) / 3600, peak_rss_GiB=peak / GiB)
    try:
        acc = validate(out, cfg)
        meta['acceptance'] = acc
        ok = proc.returncode == 0 and 'failure_reason' not in meta and acc['status'] == 'passed'
    except Exception as exc:
        meta['validation_error'] = repr(exc)
        ok = False
    if spec.get('compress', True):
        compress_closed(out, final=True)
    meta['state'] = 'completed' if ok else 'failed'
    if not ok:
        meta['log_tail'] = (out / 'simulation.log').read_text(errors='replace')[-4000:]
    write(out / 'run_manifest.json', meta)
    write(status_path, meta)
    return meta


if __name__ == '__main__':
    m = main(sys.argv[1])
    print(json.dumps({k: m.get(k) for k in ['case', 'state', 'wall_h', 'peak_rss_GiB', 'failure_reason']}))
