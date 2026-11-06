"""Deterministic, resumable serial controller for Opus B (verification_v11).

Reads queue.json (ordered list of case-spec JSON paths) on every iteration, so
cases can be appended without restarting. Exactly one solver at a time (CPU5).
A case whose run directory already exists is never relaunched: if it has a
terminal status it is skipped, otherwise it is recorded as interrupted. After a
completed run the metric extractor is run into ROOT/analysis/<case>.
Single-instance via flock on ROOT/controller.lock.
"""
from pathlib import Path
import datetime, fcntl, json, os, subprocess, sys, time

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path('/tmp/zhixin_verification_v11_20261030')
PY = '/home/zhixin/micromamba/envs/vasca311/bin/python3'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def write(p, d):
    p = Path(p)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(d, indent=1))
    tmp.replace(p)


def main():
    lock = open(ROOT / 'controller.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    st = {'controller_pid': os.getpid(), 'started_utc': utc(), 'state': 'running', 'done': [], 'failed': [], 'current': None}
    while True:
        queue = json.loads((ROOT / 'queue.json').read_text())
        todo = None
        st['done'], st['failed'], st['pending'] = [], [], []
        for spec_path in queue:
            spec = json.loads(Path(spec_path).read_text())
            name = spec['name']
            sp = ROOT / 'status' / f'{name}.json'
            s = json.loads(sp.read_text()) if sp.exists() else None
            if s and s.get('state') == 'completed':
                if spec.get('extract', True) and not (ROOT / 'analysis' / name / 'summary.json').exists():
                    todo = todo or ('extract', spec_path, spec)
                st['done'].append(name)
            elif s and s.get('state') in ('failed', 'interrupted'):
                st['failed'].append(name)
            elif (SCRATCH / 'runs' / name).exists():
                if s is None:
                    s = {'case': name}
                s.update(state='interrupted', updated_utc=utc(), note='run dir exists without live runner; not relaunched')
                write(sp, s)
                st['failed'].append(name)
            else:
                st['pending'].append(name)
                todo = todo or ('run', spec_path, spec)
        if todo is None:
            st.update(state='idle_queue_exhausted', current=None, updated_utc=utc())
            write(ROOT / 'controller_status.json', st)
            if (ROOT / 'STOP_WHEN_IDLE').exists():
                break
            time.sleep(60)
            continue
        kind, spec_path, spec = todo
        st.update(current={'kind': kind, 'case': spec['name']}, updated_utc=utc(), state='running')
        write(ROOT / 'controller_status.json', st)
        if kind == 'run':
            with open(ROOT / 'logs' / f"{spec['name']}.runner.log", 'a') as log:
                subprocess.run([PY, str(ROOT / 'remote' / 'run_case.py'), spec_path], stdout=log, stderr=subprocess.STDOUT)
        else:
            out = ROOT / 'analysis' / spec['name']
            with open(ROOT / 'logs' / f"{spec['name']}.extract.log", 'a') as log:
                r = subprocess.run(['taskset', '-c', str(spec['cpu']), 'nice', '-n', '10', PY, str(ROOT / 'tools' / 'metrics.py'),
                                    str(SCRATCH / 'runs' / spec['name']), str(out)], stdout=log, stderr=subprocess.STDOUT)
            if r.returncode:
                sp = ROOT / 'status' / f"{spec['name']}.json"
                s = json.loads(sp.read_text())
                s['extraction_failed_utc'] = utc()
                write(sp, s)
                (out).mkdir(parents=True, exist_ok=True)
                (out / 'summary.json').write_text(json.dumps({'status': 'extraction_failed', 'see_log': f"logs/{spec['name']}.extract.log"}))
    st.update(state='stopped', updated_utc=utc())
    write(ROOT / 'controller_status.json', st)


if __name__ == '__main__':
    main()
