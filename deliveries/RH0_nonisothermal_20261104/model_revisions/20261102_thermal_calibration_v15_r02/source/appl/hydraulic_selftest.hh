#ifndef CYLINDER_HYDRAULIC_SELFTEST_HH
#define CYLINDER_HYDRAULIC_SELFTEST_HH
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
namespace HeterogeneityFixed {
// Probe actual volume variables and assembled storage, not a surrogate formula.
// No state is inserted into the time-dependent solution.
template<class Tag,class Problem,class GG,class SV>
int selfTest(const Problem& problem,const GG& gg,const SV& x) {
 using namespace Dumux;
 using VV=GetPropType<Tag,Properties::VolumeVariables>;
 using FS=GetPropType<Tag,Properties::FluidSystem>;
 using LR=GetPropType<Tag,Properties::LocalResidual>;
 const bool fixed=getParam<bool>("Revision.FixedHydraulics",false);
 if(!getParam<bool>("Revision.EquilibriumPrecipitation",false))
  DUNE_THROW(Dune::InvalidStateException,"Hydraulic selftest requires total-salt equilibrium storage");
 LR residual(&problem);std::array<bool,2> done{false,false};int probes=0;
 double maxSaltError=0,maxWaterError=0,maxDiffError=0;
 for(const auto& e:elements(gg.gridView())){
  auto fv=localView(gg);fv.bindElement(e);
  for(const auto& scv:scvs(fv)){
   const int side=scv.center()[0]<=.025?0:1;if(done[side])continue;
   auto es=elementSolution(e,x,gg);es[scv.localDofIndex()][3]=0;
   VV base;base.update(es,problem,e,scv);
   const auto phi0=problem.spatialParams().referencePorosity(e,scv);
   const auto k0=getParam<double>(side==0?"SpatialParams.CoarsePermeability":"SpatialParams.FinePermeability");
   const auto n0=residual.computeStorage(problem,scv,base);
   for(double equivalentSolid:{.001,.01,.1,.45}){
    if(!fixed&&equivalentSolid==.45)continue; // coupled state would have negative geometric pore volume
    es[scv.localDofIndex()][3]=equivalentSolid;VV v;v.update(es,problem,e,scv);
    const auto n=residual.computeStorage(problem,scv,v);
    const auto solid=equivalentSolid*v.solidComponentMolarDensity(0);
    const double expectedPhi=fixed?phi0:1.0-(1.0-phi0+equivalentSolid);
    if(std::abs(v.porosity()-expectedPhi)>1e-14||std::abs(v.solidVolumeFraction(0)-equivalentSolid)>1e-15)
     DUNE_THROW(Dune::InvalidStateException,"Hydraulic selftest changed pore law or lost solid inventory");
    if(fixed&&v.permeability()!=k0)DUNE_THROW(Dune::InvalidStateException,"Fixed K depends on solid");
    if(!fixed&&!(v.permeability()<base.permeability()))DUNE_THROW(Dune::InvalidStateException,"Coupled K did not decrease");
    double fluidSalt=0,fluidWater=0;
    for(int ph=0;ph<2;++ph){
     fluidSalt+=v.porosity()*v.saturation(ph)*v.molarDensity(ph)*v.moleFraction(ph,FS::NaClIdx);
     fluidWater+=v.porosity()*v.saturation(ph)*v.molarDensity(ph)*v.moleFraction(ph,FS::H2OIdx);
    }
    const auto saltErr=std::abs(n[FS::NaClIdx]-(fluidSalt+solid))/std::max(1.,std::abs(fluidSalt+solid));
    const auto waterErr=std::abs(n[FS::H2OIdx]-fluidWater)/std::max(1.,std::abs(fluidWater));
    maxSaltError=std::max(maxSaltError,saltErr);maxWaterError=std::max(maxWaterError,waterErr);
    if(saltErr>1e-12||waterErr>1e-12||n[3]!=0)
     DUNE_THROW(Dune::InvalidStateException,"Hydraulic selftest total storage inconsistent");
    if(fixed){
     if(n[FS::H2OIdx]!=n0[FS::H2OIdx]||n[FS::AirIdx]!=n0[FS::AirIdx])
      DUNE_THROW(Dune::InvalidStateException,"Fixed pore fluid storage depends on solid");
     for(int ph=0;ph<2;++ph){
      const auto db=base.effectiveDiffusionCoefficient(ph,FS::H2OIdx,FS::NaClIdx);
      const auto dn=v.effectiveDiffusionCoefficient(ph,FS::H2OIdx,FS::NaClIdx);
      maxDiffError=std::max(maxDiffError,std::abs(db-dn));
      if(dn!=db)DUNE_THROW(Dune::InvalidStateException,"Fixed pore diffusion depends on solid");
     }
    }
    ++probes;
   }
   done[side]=true;
  }
  if(done[0]&&done[1])break;
 }
 if(!done[0]||!done[1])DUNE_THROW(Dune::InvalidStateException,"Selftest did not cover both materials");
 std::ofstream out("hydraulic_selftest.json");out<<std::setprecision(17)
  <<"{\"status\":\"passed\",\"fixed\":"<<(fixed?"true":"false")
  <<",\"probes\":"<<probes<<",\"max_salt_storage_relative_error\":"<<maxSaltError
  <<",\"max_water_storage_relative_error\":"<<maxWaterError<<",\"max_fixed_diffusion_change\":"<<maxDiffError<<"}\n";
 return 0;
}
}
#endif
