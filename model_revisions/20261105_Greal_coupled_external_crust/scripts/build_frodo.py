"""Reuse the accepted portable compilation command in an isolated directory."""
from pathlib import Path
import json
import subprocess
import hashlib

root = Path(__file__).resolve().parents[1]
old = '/temp/zhixin/Greal_experimental_bottom_hpcc_20261104'
command = json.loads(Path(old, 'compile_command.json').read_text())
command = [v.replace(old, str(root)) for v in command]
(root / 'build').mkdir(exist_ok=True)
(root / 'build/command.json').write_text(json.dumps(command, indent=2))
with (root / 'build/compile.log').open('w') as log:
    result = subprocess.run(['nice', '-n', '10'] + command, stdout=log, stderr=subprocess.STDOUT)
record = {'returncode': result.returncode, 'qualified': False}
if result.returncode == 0:
    record['binary_sha256'] = hashlib.sha256((root / 'build/solver').read_bytes()).hexdigest()
(root / 'build/status.json').write_text(json.dumps(record, indent=2))
raise SystemExit(result.returncode)
