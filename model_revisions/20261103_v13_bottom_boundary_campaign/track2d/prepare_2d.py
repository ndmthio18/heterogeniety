"""Create isolated conventional 2D overlay and inputs; never mutate 3D files."""
from pathlib import Path
import shutil,json,hashlib,configparser,math
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;P=R.parent;S=R/'source/appl'
assert not (R/'build/solver').exists(), 'Do not regenerate a frozen built revision'
shutil.copytree(P/'source_filter',R/'source',dirs_exist_ok=True)
def edit(name,old,new):
 p=S/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new),newline='\n')
edit('properties.hh','using type = Dune::UGGrid<3>;','using type = Dune::UGGrid<2>;')
p=S/'properties.hh';s=p.read_text();start=s.index('template<class TypeTag>\nstruct GridGeometry<');end=s.index('template<class TypeTag>\nstruct Problem',start);s=s[:start]+s[end:];p.write_text(s,newline='\n')
edit('spatialparams.hh','return 1.0;','return getParam<Scalar>("Geometry.ExtrusionWidth", .039269908169872414);')
p=S/'problem.hh';s=p.read_text()
start=s.index('   std::ifstream in(getParam<std::string>("Revision.PortAreaFile"))');end=s.index('\n  }',start)
s=s[:start]+'   if(getParam<Scalar>("Revision.SlitWidth",0)<=0)DUNE_THROW(Dune::InvalidStateException,"Positive 2D slit width required");'+s[end:]
start=s.index('    bool found=false;for(const auto& p:portFaces_)');end=s.index('\n   }else if',start)
s=s[:start]+'''    const auto width=getParam<Scalar>("Revision.SlitWidth");
    const auto half=face.area()/2;
    active=std::max(Scalar(0),std::min(pos[0]+half,split_+width/2)-std::max(pos[0]-half,split_-width/2))/face.area();'''+s[end:]
s=s.replace('double(pos[2])','0.0').replace('+p[2]/wavelengths[j][2]','')
s=s.replace('FieldMatrix<Scalar,3,3>','FieldMatrix<Scalar,2,2>').replace('FieldVector<Scalar,3>','FieldVector<Scalar,2>')
s=s.replace('for(int i=0;i<3;++i){b[i]','for(int i=0;i<2;++i){b[i]').replace('for(int j=0;j<3;++j)a[i][j]','for(int j=0;j<2;++j)a[i][j]')
p.write_text(s,newline='\n')
p=S/'campaign_diagnostics.hh';s=p.read_text().replace("<<pos[2]<<",'<<0.0<<');p.write_text(s,newline='\n')
p=S/'geometry_audit.hh';s=p.read_text();s=s.replace('double volume=0','const double width=Dumux::getParam<double>("Geometry.ExtrusionWidth",.039269908169872414);\n double volume=0').replace('const auto v=scv.volume();','const auto v=scv.volume()*width;').replace("<<c[2]<<",'<<0.0<<').replace('k<3','k<2').replace('+=f.area()','+=f.area()*width').replace('contact-.05*','contact-width*');p.write_text(s,newline='\n')
# Unit-depth 2D geometry extruded by A_cylinder / W. Exact nominal circular top area,
# no circular-polygon correction. Missing front/back heat exchange is explicit.
width=math.pi*.025**2/.05
geom=pd.read_csv(P/'baseline_reference/cell_geometry.csv');ys=sorted(set(np.round(geom.ymin_m,12)).union(np.round(geom.ymax_m,12)));assert len(ys)==41 and min(np.diff(ys))>1e-6
def mesh(name,nx,refine=False,filter=False):
 y=np.array(ys)
 if refine:y=np.sort(np.r_[y,(y[:-1]+y[1:])/2])
 if filter:y=np.r_[np.linspace(-.0045,0,7)[:-1],y]
 x=np.linspace(0,.05,nx+1);nodes=[(a,b) for b in y for a in x];els=[]
 for j in range(len(y)-1):
  for i in range(nx):
   k=j*(nx+1)+i+1;els.append((k,k+1,k+nx+2,k+nx+1))
 lines=['$MeshFormat','2.2 0 8','$EndMeshFormat','$Nodes',str(len(nodes))]
 lines += [f'{i+1} {a:.17g} {b:.17g} 0' for i,(a,b) in enumerate(nodes)]
 lines+=['$EndNodes','$Elements',str(len(els))]+[f'{i+1} 3 2 1 1 '+ ' '.join(map(str,e)) for i,e in enumerate(els)]+['$EndElements']
 (R/'inputs'/name).write_text('\n'.join(lines)+'\n',newline='\n')
 return len(els)
sizes={}
for nx,ref,label in [(100,False,''),(200,True,'_refined')]:
 for filt in [False,True]:
  name=('filter' if filt else 'sand')+label+'.msh';sizes[name]=mesh(name,nx,ref,filt)
mesh('reaction2d.msh',2,False,False)
base=configparser.ConfigParser();base.optionxform=str;base.read(P/'inputs/B0.input')
def inp(name,kind='B0',end=633600,hydro=False,dt=300,refined=False,scale=1):
 c=configparser.ConfigParser();c.optionxform=str;c.read_dict({s:dict(base[s]) for s in base.sections()})
 c['Problem']['Name']=name;c['TimeLoop']['TEnd']=str(end);c['TimeLoop']['MaxTimeStepSize']=str(dt)
 c['Geometry']={'ExtrusionWidth':str(width*scale)};c['Grid']['File']=('filter' if kind.startswith('G') else 'sand')+('_refined' if refined else '')+'.msh'
 c['Revision']['WaterFluxAreaCorrection']='1';c['Revision']['ExplicitFilter']=str(kind.startswith('G')).lower()
 c['Revision']['FilterHydraulicResistance']=str([0,.1,1,10][int(kind[1])]*288856.0397652994) if kind.startswith('B') else '0'
 if kind.startswith('G'):
  d={'G1':.002,'G2':.005,'G3':.01}[kind];c['Revision']['SlitWidth']=str(math.pi*d*d/4/width)
  c['SpatialParams']['FilterPorosity']='.35';c['SpatialParams']['FilterPermeability']='1.7333127738454676e-11';c['SpatialParams']['FilterPcGroup']='SpatialParams.CoarseMaterial'
 if hydro:c['Revision']['PreEquilibrationSeconds']=str(end);c['Revision']['PerturbationStd']='0'
 with (R/'inputs'/f'{name}.input').open('w') as f:c.write(f)
 return c
for kind in ['B0','B1','B2','B3','G1','G2','G3']:
 inp(kind,kind);inp(kind+'_hydro',kind,7200,True);inp(kind+'_short',kind,14400)
for kind in ['B0','G1','G2']:
 inp(kind+'_dt150',kind,14400,dt=150);inp(kind+'_refined',kind,14400,refined=True)
inp('B0_width2','B0',14400,scale=2)
for old in ['Precipitate_dt30','Precipitate_dt15','Dissolve_dt30','Dissolve_dt15','RemainSolid_dt30','RemainSolid_dt15','Recovery_injected','Selftest_fixed','Selftest_coupled']:
 c=configparser.ConfigParser();c.optionxform=str;c.read(P/'inputs'/f'{old}.input');c['Grid']['File']='reaction2d.msh';c['Geometry']={'ExtrusionWidth':str(width)}
 with (R/'inputs'/f'{old}.input').open('w') as f:c.write(f)
for f in ['water_flux_zero_storage.txt','forcing_provenance.json']:shutil.copy2(P/'inputs'/f,R/'inputs'/f)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'inputs').iterdir() if p.is_file()};(R/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
(R/'results/geometry_preparation.json').write_text(json.dumps(dict(dimension=2,width_m=.05,height_m=.04,extrusion_m=width,cells=sizes,slit_widths_m={g:math.pi*d*d/4/width for g,d in [('G1',.002),('G2',.005),('G3',.01)]},normalization='Exact nominal cylinder top area; unit-depth planar physics, no front/back wall heat exchange',reference_resistance_Pa_s_m=288856.0397652994),indent=2))
print(sizes)
