"""Preserve all original sand cells; extrude the same base 4.5 mm downward.
Circular port/face intersection uses exact line and circle-sector integrals.
"""
from pathlib import Path
import numpy as np,json,math,hashlib,configparser
R=Path(__file__).resolve().parent;I=R/'inputs'
lines=(I/'cylinder.msh').read_text().splitlines();i=lines.index('$Nodes');nn=int(lines[i+1]);nodes={int(z[0]):np.array(list(map(float,z[1:]))) for z in (s.split() for s in lines[i+2:i+2+nn])}
i=lines.index('$Elements');ne=int(lines[i+1]);elems=[list(map(int,s.split())) for s in lines[i+2:i+2+ne]]
bottom=[]
for e in elems:
 n=e[3+e[2]:];half=len(n)//2
 if all(abs(nodes[k][1])<1e-12 for k in n[:half]):bottom.append((e[1],n[:half]))
assert len(bottom)==768
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def area(poly):return abs(sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))/2)
def overlap(poly,r):
 total=0.
 for a,b in zip(poly,poly[1:]+poly[:1]):
  d=b-a;aa=d@d;bb=2*(a@d);cc=a@a-r*r;disc=bb*bb-4*aa*cc;cuts=[0.,1.]
  if disc>0:cuts+= [v for v in [(-bb-math.sqrt(disc))/(2*aa),(-bb+math.sqrt(disc))/(2*aa)] if 0<v<1]
  cuts=sorted(cuts)
  for t,u in zip(cuts,cuts[1:]):
   p=a+t*d;q=a+u*d;mid=(p+q)/2
   total+=cross(p,q)/2 if mid@mid<r*r else r*r*math.atan2(cross(p,q),p@q)/2
 return abs(total)
def centre(poly):
 a=poly[0];b=poly[1]-a;c=poly[2]-a
 return a+np.linalg.solve(np.array([b,c])*2,np.array([b@b,c@c]))
evidence=[]
for layers in [6,12]:
 ns={k:v.copy() for k,v in nodes.items()};es=[e[:] for e in elems];baseids=sorted({k for _,ks in bottom for k in ks});old={k:k for k in baseids}
 for j in range(1,layers+1):
  new={}
  for k in baseids:
   nk=len(ns)+1;v=nodes[k].copy();v[1]=-.0045*j/layers;ns[nk]=v;new[k]=nk
  for typ,ks in bottom:es.append([len(es)+1,typ,0]+[new[k] for k in ks]+[old[k] for k in ks])
  old=new
 p=I/f'filter_{layers}layers.msh'
 with p.open('w') as f:
  f.write('$MeshFormat\n2.2 0 8\n$EndMeshFormat\n$Nodes\n'+str(len(ns))+'\n')
  for k,v in ns.items():f.write(str(k)+' '+' '.join(format(x,'.17g') for x in v)+'\n')
  f.write('$EndNodes\n$Elements\n'+str(len(es))+'\n')
  for e in es:f.write(' '.join(map(str,e))+'\n')
  f.write('$EndElements\n')
 evidence.append(dict(file=p.name,cells=len(es),sand_cells_unchanged=ne,filter_layers=layers,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
ports=[]
for name,diam in [('G1',.002),('G2',.005),('G3',.01),('Gdistributed',.1)]:
 rows=[]
 for _,ks in bottom:
  poly=[nodes[k][[0,2]]-np.array([.025,0]) for k in ks];a=area(poly);cut=overlap(poly,diam/2);cut=0. if cut<a*1e-12 else (a if cut>a*(1-1e-12) else cut);c=centre(poly)+np.array([.025,0]);rows.append((c[0],c[1],min(1.,max(0.,cut/a)),a))
 expected=math.pi*(diam/2)**2 if diam<.05 else sum(x[3] for x in rows)
 got=sum(x[2]*x[3] for x in rows);assert abs(got/expected-1)<1e-10,(got,expected)
 np.savetxt(I/f'{name}_port.txt',np.array(rows)[:,:3],fmt='%.17g')
 ports.append(dict(case=name,diameter_m=diam,active_area_m2=got,analytic_area_m2=expected,cut_faces=int(sum(0<x[2]<1 for x in rows)),active_faces=int(sum(x[2]>0 for x in rows)),method='exact circle/polygon overlap; fractional Neumann face integration, unresolved subface pressure remains a discretization limitation'))
 cfg=configparser.ConfigParser();cfg.optionxform=str;cfg.read(I/'B0.input');cfg['Grid']['File']='filter_6layers.msh';cfg['Problem']['Name']=name
 ref=json.loads((R/'REFERENCE_RESISTANCE.json').read_text());cfg['Revision']['ExplicitFilter']='true';cfg['Revision']['PortAreaFile']=f'{name}_port.txt';cfg['Revision']['FilterHydraulicResistance']='0';cfg['SpatialParams']['FilterPorosity']='0.35';cfg['SpatialParams']['FilterPermeability']=str(ref['filter_K_m2']);cfg['SpatialParams']['FilterPcGroup']='SpatialParams.FilterMaterial';cfg['SpatialParams.FilterMaterial']=dict(cfg['SpatialParams.CoarseMaterial'])
 for suffix,end in [('',633600),('_hydro',7200),('_short',14400),('_dt150',14400),('_z12',14400)]:
  c=configparser.ConfigParser();c.optionxform=str;c.read_dict({s:dict(cfg[s]) for s in cfg.sections()});c['TimeLoop']['TEnd']=str(end);c['Problem']['Name']=name+suffix
  if suffix=='_hydro':c['Revision']['PerturbationStd']='0'
  if suffix=='_dt150':c['TimeLoop']['MaxTimeStepSize']='150'
  if suffix=='_z12':c['Grid']['File']='filter_12layers.msh'
  with (I/f'{name+suffix}.input').open('w') as f:c.write(f)
(R/'results/geometry_preparation.json').write_text(json.dumps(dict(meshes=evidence,ports=ports,assumptions='port at filter bottom; no unmeasured plenum; filter phi=.35, K matched initial B2 resistance; inherited coarse retention law and granite inert thermal surrogate (not measured P3 glass properties)'),indent=2))
print(json.dumps(ports,indent=2))
