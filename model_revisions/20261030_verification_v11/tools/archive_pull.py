"""Pull completed v11 raw run directories from liqin scratch to D: and verify.

For each case: remote `sha256sum` of every file -> scp -r -> local SHA256 of every
file must match; gz frames are additionally checked against compressed_fields.jsonl
(gzip SHA256 recorded at compression time). Writes runs_archive/<case>/ARCHIVE_MANIFEST.json.
Never deletes anything (remote deletion, if ever needed, is a separate explicit step).
Usage: python archive_pull.py CASE [CASE ...] | --all-completed
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCR = '/tmp/zhixin_verification_v11_20261030/runs'
R = '/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def ssh(cmd, timeout=600):
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'liqin', cmd], capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout


def pull(case):
    dst = ROOT / 'runs_archive' / case
    man = dst / 'ARCHIVE_MANIFEST.json'
    if man.exists() and json.loads(man.read_text()).get('status') == 'verified':
        return json.loads(man.read_text())
    remote = {}
    for line in ssh(f'cd {SCR}/{case} && sha256sum *').splitlines():
        h, name = line.split(None, 1)
        remote[name.lstrip('*')] = h
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f'liqin:{SCR}/{case}/*', str(dst)], check=True, timeout=7200)
    bad = [n for n, h in remote.items() if not (dst / n).exists() or sha(dst / n) != h]
    gz_bad = []
    cf = dst / 'compressed_fields.jsonl'
    if cf.exists():
        for line in cf.read_text().splitlines():
            e = json.loads(line)
            if remote.get(e['file']) != e['gzip_sha256']:
                gz_bad.append(e['file'])
    res = {'case': case, 'files': len(remote), 'bytes': sum((dst / n).stat().st_size for n in remote if (dst / n).exists()),
           'mismatches': bad, 'gzip_record_mismatches': gz_bad, 'remote_path': f'{SCR}/{case}',
           'status': 'verified' if not bad and not gz_bad else 'mismatch', 'sha256': remote}
    man.write_text(json.dumps(res, indent=1))
    return res


if __name__ == '__main__':
    cases = sys.argv[1:]
    if cases == ['--all-completed']:
        st = json.loads(ssh(f'python3 -c "import json,glob,os;print(json.dumps({{os.path.basename(f)[:-5]:json.load(open(f)).get(\'state\') for f in glob.glob(\'{R}/status/*.json\')}}))"'))
        cases = sorted(k for k, v in st.items() if v == 'completed')
    for c in cases:
        r = pull(c)
        print(json.dumps({k: r[k] for k in ['case', 'files', 'bytes', 'status']}))
