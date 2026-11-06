"""Generate v10 inputs by line edits of the frozen v08 Dry_trial02_r02 input.
Only Name, TEnd, PerturbationStd and the explicit switch keys may differ."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
BASE=(R/'inputs/Dry_trial02_r02.input').read_text()
SWITCH={'C1B1':(True,1),'C0B1':(False,1),'C1B0':(True,0),'C0B0':(False,0)}
def make(name,tend,switch=None,sigma=None,selftest=False):
 lines=BASE.splitlines();out=[];section=None
 for line in lines:
  s=line.strip()
  if s.startswith('['):section=s
  key=s.split('=')[0].strip() if '=' in s else None
  if section=='[TimeLoop]' and key=='TEnd':line=f'TEnd = {tend}'
  if section=='[Problem]' and key=='Name':line=f'Name = {name}'
  if section=='[Revision]' and key=='PerturbationStd' and sigma is not None:line=f'PerturbationStd = {sigma}'
  out.append(line)
  if section=='[Revision]' and key=='FilmRH':
   if switch is not None:
    c,b=SWITCH[switch];out+=[f'InterfaceExchangeEnabled = {"true" if c else "false"}',f'SalinityBuoyancyScale = {b}']
   if selftest:out.append('CausalSelfTest = true')
 text='\n'.join(out)+'\n';(R/'inputs'/f'{name}.input').write_text(text,newline='\n')
 return name
cases={}
for k in SWITCH:cases[make(f'SelfTest_{k}',93600,k,selftest=True)]='selftest'
cases[make('Hydrostatic_C1B1',7200,'C1B1',sigma=0)]='hydrostatic'
cases[make('Hydrostatic_C1B0',7200,'C1B0',sigma=0)]='hydrostatic'
cases[make('Hydrostatic_C0B0',7200,'C0B0',sigma=0)]='hydrostatic'
cases[make('PrefixRegression',7800)]='prefix_regression'
for k in ['C0B1','C1B0','C0B0']:cases[make(f'Short_{k}',9000,k)]='short_check'
for k in SWITCH:cases[make(f'{k}_24h',93600,k)]='production'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'inputs/input_manifest.json').write_text(json.dumps({n:{'role':r,'sha256':sha(R/'inputs'/f'{n}.input')} for n,r in cases.items()}|{'_base':{'file':'Dry_trial02_r02.input','sha256':sha(R/'inputs/Dry_trial02_r02.input')}},indent=2))
print(json.dumps(cases,indent=1))
