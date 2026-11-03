from pathlib import Path
import shutil,difflib,json,hashlib
R=Path(__file__).resolve().parent;S=R/'source_filter';shutil.copytree(R/'source_baseline',S)
def change(p,a,b):
 s=p.read_text();assert a in s,(p,a);p.write_text(s.replace(a,b),encoding='utf-8')
p=S/'appl/spatialparams.hh'
change(p,', finePcKrSwCurve_(getParam<std::string>("SpatialParams.FinePcGroup", "SpatialParams"))',', finePcKrSwCurve_(getParam<std::string>("SpatialParams.FinePcGroup", "SpatialParams"))\n    , filterPcKrSwCurve_(getParam<std::string>("SpatialParams.FilterPcGroup", "SpatialParams.CoarseMaterial"))')
change(p,'return isCoarse_(globalPos)\n            ?', 'return isFilter(globalPos) ? makeFluidMatrixInteraction(filterPcKrSwCurve_) : isCoarse_(globalPos)\n            ?')
change(p,'bool fixedHydraulics() const { return fixedHydraulics_; }','bool fixedHydraulics() const { return fixedHydraulics_; }\n    bool isFilter(const GlobalPosition& p) const {return explicitFilter_ && p[1]<-1e-10;}\n    Scalar registeredPermeability(const GlobalPosition& p)const{return referencePermeabilityAtPos_(p);}')
change(p,'return isCoarse_(globalPos) ? coarsePorosity_ : finePorosity_;','return isFilter(globalPos) ? filterPorosity_ : (isCoarse_(globalPos) ? coarsePorosity_ : finePorosity_);')
change(p,'return isCoarse_(globalPos) ? coarsePermeability_ : finePermeability_;','return isFilter(globalPos) ? filterPermeability_ : (isCoarse_(globalPos) ? coarsePermeability_ : finePermeability_);')
change(p,'const PcKrSwCurve finePcKrSwCurve_;','const PcKrSwCurve finePcKrSwCurve_;\n    const PcKrSwCurve filterPcKrSwCurve_;\n    const bool explicitFilter_=getParam<bool>("Revision.ExplicitFilter",false);\n    const Scalar filterPorosity_=getParam<Scalar>("SpatialParams.FilterPorosity",.35);\n    const Scalar filterPermeability_=getParam<Scalar>("SpatialParams.FilterPermeability",1e-11);')
p=S/'appl/problem.hh'
change(p,'#include <random>','#include <random>\n#include <sstream>')
change(p,'level_=getParam<Scalar>("Reservoir.LevelAboveSandBottom",.02)+gg->bBoxMin()[1];','level_=getParam<Scalar>("Reservoir.LevelAboveSandBottom",.02)+(explicitFilter_?0.:gg->bBoxMin()[1]);')
change(p,'inlet_=getParam<Scalar>("Problem.InletSize",.002);','''inlet_=getParam<Scalar>("Problem.InletSize",.002);
  if(explicitFilter_){
   if(std::abs(gg->bBoxMin()[1]+.0045)>1e-10 || resistance_!=0)
    DUNE_THROW(Dune::InvalidStateException,"Explicit filter geometry must be 4.5 mm; additional Robin resistance forbidden");
   std::ifstream in(getParam<std::string>("Revision.PortAreaFile"));double x,z,a;
   while(in>>x>>z>>a){if(a<0||a>1)DUNE_THROW(Dune::InvalidStateException,"Invalid circular port face fraction");portFaces_.push_back({x,z,a});}
   if(portFaces_.size()!=768)DUNE_THROW(Dune::InvalidStateException,"Incomplete port area map");
  }''')
change(p,'if(supply_=="CentralAperture"){','if(explicitFilter_){\n    bool found=false;for(const auto& p:portFaces_)if(std::hypot(pos[0]-p[0],pos[2]-p[1])<1e-10){active=p[2];found=true;break;}\n    if(!found)DUNE_THROW(Dune::InvalidStateException,"No matching 3D port face");\n   }else if(supply_=="CentralAperture"){')
change(p,'const auto k0=getParam<Scalar>(scv.center()[0]<=split_?"SpatialParams.CoarsePermeability":"SpatialParams.FinePermeability");','const auto k0=this->spatialParams().registeredPermeability(scv.center());')
# Preserve the original sand perturbation: exclude added filter from normalization and correction.
change(p,'const auto p=scv.center();Scalar value=0;','const auto p=scv.center();if(this->spatialParams().isFilter(p))continue;Scalar value=0;')
change(p,'for(auto& v:noise)v=sigma_*(v-mean)/rms;','std::vector<bool> sand(x.size(),true);\n  for(const auto& e:elements(this->gridGeometry().gridView())){auto fv=localView(this->gridGeometry());fv.bindElement(e);for(const auto& scv:scvs(fv))sand[scv.dofIndex()]=!this->spatialParams().isFilter(scv.center());}\n  for(std::size_t i=0;i<noise.size();++i)noise[i]=sand[i]?sigma_*(noise[i]-mean)/rms:0.;')
change(p,'candidate[i][salt]+=noise[i]-shift;','if(sand[i])candidate[i][salt]+=noise[i]-shift;')
change(p,'private:\n const bool equilibriumPrecipitation_', '#include "campaign_diagnostics.hh"\nprivate:\n const bool explicitFilter_=getParam<bool>("Revision.ExplicitFilter",false);\n std::vector<std::array<double,3>> portFaces_;\n const bool equilibriumPrecipitation_')
p=S/'appl/geometry_audit.hh'
change(p,'else if(f.ipGlobal()[1]<1e-9)bottom+=f.area();','else if(f.ipGlobal()[1]<gg.bBoxMin()[1]+1e-9)bottom+=f.area();')
change(p,'std::abs(contact-.002)>1e-10','std::abs(contact-.05*(gg.bBoxMax()[1]-gg.bBoxMin()[1]))>1e-10')
p=S/'appl/main.cc'
change(p,'problem->record(initial,start,0);','problem->record(initial,start,0);problem->campaignAudit(x,*gv,start,0,false,true);')
change(p,'problem->record(a,acceptedTime,acceptedDt);','problem->record(a,acceptedTime,acceptedDt);problem->campaignAudit(x,*gv,acceptedTime,acceptedDt);')
change(p,'if(problem->seed(x,*gv))gv->advanceTimeStep();','if(problem->seed(x,*gv)){gv->advanceTimeStep();problem->campaignAudit(x,*gv,clock->time(),0,true);}')
change(p,'vtk.write(clock->time());','vtk.write(clock->time());problem->campaignAudit(x,*gv,clock->time(),0,false,true,true);')
shutil.copy2(R/'campaign_diagnostics.hh',S/'appl/campaign_diagnostics.hh')
diff=[]
for p in S.rglob('*'):
 if p.is_file():
  rel=p.relative_to(S);old=R/'source_baseline'/rel
  if not old.exists() or p.read_bytes()!=old.read_bytes():diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile='baseline/'+rel.as_posix(),tofile='filter/'+rel.as_posix()))
(R/'provenance/filter_implementation.patch').write_text(''.join(diff),encoding='utf-8')
(R/'provenance/filter_source_manifest.json').write_text(json.dumps({p.relative_to(S).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in S.rglob('*') if p.is_file()},indent=2))
