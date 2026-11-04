from pathlib import Path
import os,signal,json,datetime,subprocess,hashlib
old=Path('/temp/zhixin/heterogeneity_thermal_calibration_v15_20261102')
new=Path(__file__).resolve().parent
pid=2354572
assert Path(f'/proc/{pid}/cwd').resolve()==old
assert b'calibrate.py' in Path(f'/proc/{pid}/cmdline').read_bytes()
status=json.loads((old/'calibration_status.json').read_text())
assert status['state']=='gates_running',status
# Stop only the scheduler. Its already-started reference gate finishes independently.
os.kill(pid,signal.SIGTERM)
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='User requested verified accelerated profile',previous_status=status,replacement=str(new),reference_solver_pid=2355273,reference_solver_allowed_to_finish=True)
(old/'superseded_by_accelerated.json').write_text(json.dumps(record,indent=2))
(old/'calibration_status_before_supersession.json').write_text(json.dumps(status,indent=2))
(old/'calibration_status.json').write_text(json.dumps(dict(state='superseded',**record),indent=2))
with (new/'controller.log').open('w') as log:
 p=subprocess.Popen([str(old/'venv/bin/python'),str(new/'calibrate.py')],cwd=new,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
record['new_controller_pid']=p.pid
(new/'deployment.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
