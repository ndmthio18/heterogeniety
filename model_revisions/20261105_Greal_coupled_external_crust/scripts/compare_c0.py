from pathlib import Path
import csv,json,math
root=Path('/WORK/hulm_work/zhixin/Greal_coupled_external_crust_20261105')
dirs=[root/'gates'/n for n in ('C0_original','C0_patched')]
for d in dirs:
    status=json.loads((d/'run_status.json').read_text())
    if status.get('status')!='completed' or abs(status['time_s']-7800)>1e-8:
        raise RuntimeError('Endpoint not accepted')
results={}
for name in ('budget.csv','film_budget.csv','mineral_budget.csv','thermal_budget.csv','depth_profiles_compact.csv'):
    tables=[]
    for d in dirs:
        with (d/name).open() as f: tables.append(list(csv.DictReader(f)))
    if len(tables[0])!=len(tables[1]): raise RuntimeError('Row count mismatch '+name)
    maximum=0.
    for a,b in zip(*tables):
        if a.keys()!=b.keys(): raise RuntimeError('Schema mismatch')
        for key in a:
            try: x,y=float(a[key]),float(b[key])
            except ValueError:
                if a[key]!=b[key]: raise RuntimeError('Label mismatch')
                continue
            if not math.isfinite(x) or not math.isfinite(y): raise RuntimeError('Nonfinite '+key)
            maximum=max(maximum,abs(x-y)/max(1.,abs(x),abs(y)))
    results[name]={'rows':len(tables[0]),'max_scaled_difference':maximum}
passed=all(r['max_scaled_difference']<=1e-7 for r in results.values())
record={'passed':passed,'window':'2h equilibration plus 10min evaporation; pre-precipitation only','metrics':results}
(root/'c0_comparison.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
if not passed: raise SystemExit(1)
