#ifndef HETEROGENEITY_REVISED_PROBLEM_HH
#define HETEROGENEITY_REVISED_PROBLEM_HH
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <memory>
#include <random>
#include <dumux/common/properties.hh>
#include <dumux/common/parameters.hh>
#include <dumux/common/boundarytypes.hh>
#include <dumux/common/timeloop.hh>
#include <dumux/porousmediumflow/problem.hh>
#include <dumux/porousmediumflow/nonisothermal/localresidual.hh>
#include <dumux/material/constraintsolvers/misciblemultiphasecomposition.hh>
#include "revision_support.hh"
#include "water_activity.hh"
#include "phase_equilibrium.hh"
#include "precipitation_equilibrium.hh"
namespace Dumux {
template<class TypeTag>
class SaltExperimentsProblem:public PorousMediumFlowProblem<TypeTag> {
 using Parent=PorousMediumFlowProblem<TypeTag>;
 using Scalar=GetPropType<TypeTag,Properties::Scalar>;
 using GG=GetPropType<TypeTag,Properties::GridGeometry>;
 using FS=GetPropType<TypeTag,Properties::FluidSystem>;
 using State=GetPropType<TypeTag,Properties::FluidState>;
 using VV=GetPropType<TypeTag,Properties::VolumeVariables>;
 using Ind=typename GetPropType<TypeTag,Properties::ModelTraits>::Indices;
 using PV=GetPropType<TypeTag,Properties::PrimaryVariables>;
 using SV=GetPropType<TypeTag,Properties::SolutionVector>;
 using FV=typename GG::LocalView;
 using EV=typename GetPropType<TypeTag,Properties::GridVolumeVariables>::LocalView;
 using FC=typename GetPropType<TypeTag,Properties::GridFluxVariablesCache>::LocalView;
 using Face=typename GG::SubControlVolumeFace;
 using Elem=typename GG::GridView::template Codim<0>::Entity;
 using FluxVars=GetPropType<TypeTag,Properties::FluxVariables>;
 using Cache=typename FS::ParameterCache;
 static constexpr int water=FS::H2OIdx,air=FS::AirIdx,salt=FS::NaClIdx,liq=FS::liquidPhaseIdx,gas=FS::gasPhaseIdx,solidEq=FS::numComponents;
public:
 using NumEqVector=Dumux::NumEqVector<PV>;
 using BoundaryTypes=Dumux::BoundaryTypes<GetPropType<TypeTag,Properties::ModelTraits>::numEq()>;
 struct Audit {
  std::array<double,3> n{},out{},bottomOut{};
  double topAir=0;std::vector<std::array<double,14>> filmFaces;
  std::array<double,2> topWater{};
  double dissolved=0,solid=0,coarse=0,fine=0,interfaceAdv=0,interfaceDiff=0,bottomCoarse=0,bottomFine=0;
  double smin=1,pmin=1,precip=0,cmax=0,mmax=0,ncpmax=0,solidmin=0;
  double coarseSolid=0,fineSolid=0;
#if NONISOTHERMAL
  double energy=0,energyOut=0,tmin=1e100,tmax=-1e100;
#endif
 };
 SaltExperimentsProblem(std::shared_ptr<const GG> gg):Parent(gg) {
  name_=getParam<std::string>("Problem.Name","revised");
  temperature_=getParam<Scalar>("Reservoir.Temperature",293.15);
  patm_=getParam<Scalar>("Reservoir.AtmosphericPressure",1e5);
  level_=getParam<Scalar>("Reservoir.LevelAboveSandBottom",.02)+gg->bBoxMin()[1];
  split_=getParam<Scalar>("SpatialParams.SplitCoordinate",.025);
  coarseWaterMultiplier_=getParam<Scalar>("Revision.CoarseWaterFluxMultiplier",1.);
  const auto coarseArea=(split_-gg->bBoxMin()[0])/(gg->bBoxMax()[0]-gg->bBoxMin()[0]);
  fineWaterMultiplier_=HeterogeneityRevision::fineFluxMultiplier(coarseWaterMultiplier_,coarseArea);
  pre_=getParam<Scalar>("Revision.PreEquilibrationSeconds",7200);
  sigma_=getParam<Scalar>("Revision.PerturbationStd",0);
  constantWater_=getParam<Scalar>("Revision.WaterMassFlux",0);
  supply_=getParam<std::string>("Revision.SupplyMode","DistributedReservoir");
  resistance_=getParam<Scalar>("Revision.FilterHydraulicResistance",0);
  inlet_=getParam<Scalar>("Problem.InletSize",.002);
  coarseBL_=getParam<Scalar>("FreeFlow.CoarseBoundaryLayerThickness",.012642);
  fineBL_=getParam<Scalar>("FreeFlow.FineBoundaryLayerThickness",.003019);
  relativeHumidity_=getParam<Scalar>("FreeFlow.RelativeHumidity",.4);
  activityMode_=getParam<bool>("Revision.ActivityWeightedEvaporation",false);
  activityRH_=getParam<Scalar>("Revision.ActivityRelativeVaporPressure",0.);
  if(activityMode_&&(NONISOTHERMAL||coarseWaterMultiplier_!=1.||activityRH_<0||activityRH_>=1))
   DUNE_THROW(Dune::InvalidStateException,"Activity weighting requires isothermal mode, unit static partition and RH in [0,1)");
  wallK_=getParam<Scalar>("Problem.PlexiglassThermalConductivity",.184);
  wallD_=getParam<Scalar>("Problem.PlexiglassThickness",.005);
  if(supply_!="DistributedReservoir"&&supply_!="CentralAperture")DUNE_THROW(Dune::InvalidStateException,"Unknown supply mode");
  auto mode=getParam<std::string>("Revision.WaterForcingMode","ConstantWaterMass");
  filmMode_=mode=="FilmTransfer";
  filmDelta_=getParam<Scalar>("Revision.FilmThickness",.0083);filmRH_=getParam<Scalar>("Revision.FilmRH",0.);
  if(filmMode_&&(!FS::unifiedWaterActivity()||activityMode_||filmDelta_<=0||filmRH_<0||filmRH_>=1||coarseWaterMultiplier_!=1.))DUNE_THROW(Dune::InvalidStateException,"Film mode requires unified activity, positive thickness, valid RH and no normalized/static partition");
  seriesMode_=mode=="IntervalWaterMass";
  if(!filmMode_&&!seriesMode_&&mode!="ConstantWaterMass")DUNE_THROW(Dune::InvalidStateException,"Unknown forcing mode");
  if(seriesMode_)series_.load(getParam<std::string>("Revision.WaterForcingFile"));
  FS::init(273.15,323.15,100,0.,2e6,200);
  if(filmMode_){
   filmPsat_=Components::H2O<Scalar>::vaporPressure(temperature_);
   filmYRef_=filmRH_*filmPsat_/patm_;filmXRef_=gasWaterMassFraction_(filmYRef_);
   State ref;for(int ph=0;ph<2;++ph){ref.setTemperature(ph,temperature_);ref.setPressure(ph,patm_);ref.setSaturation(ph,ph==gas?1:0);for(int k=0;k<3;++k)ref.setMoleFraction(ph,k,0);}
   ref.setMoleFraction(gas,water,filmYRef_);ref.setMoleFraction(gas,air,1-filmYRef_);
   filmRhoRef_=FS::density(ref,gas);filmD_=FS::binaryDiffusionCoefficient(ref,gas,water,air);
   relativeHumidity_=filmRH_;
   std::cout<<std::setprecision(17)<<"PREDICTIVE_FILM delta_m="<<filmDelta_<<" RH="<<filmRH_<<" D="<<filmD_<<" rho_ref="<<filmRhoRef_<<" total_constraint=none unified_activity=true"<<std::endl;
  }
  Scalar a=.000001,b=.09,target=getParam<Scalar>("Reservoir.Molarity",1.);
  for(int i=0;i<60;++i){auto xs=(a+b)/2;auto st=reservoirState_(xs);if(xs*FS::molarDensity(st,liq)/1000<target)a=xs;else b=xs;}
  reservoir_=reservoirState_((a+b)/2);rhoRes_=FS::density(reservoir_,liq);molarRes_=FS::molarDensity(reservoir_,liq);
  std::cout<<std::setprecision(15)<<"REVISED_CONFIG p0s1 reservoir_M="<<reservoir_.moleFraction(liq,salt)*molarRes_/1000
   <<" xSalt="<<reservoir_.moleFraction(liq,salt)<<" xAir="<<reservoir_.moleFraction(liq,air)<<" rho="<<rhoRes_
   <<" level="<<level_<<" pre_s="<<pre_<<" supply="<<supply_<<" R_filter="<<resistance_<<" forcing="<<mode<<std::endl;
  std::cout<<"CONTROLLED_SENSITIVITY coarse_water_factor="<<coarseWaterMultiplier_<<" fine_water_factor="<<fineWaterMultiplier_
   <<" liquid_salt_binary_D="<<FS::binaryDiffusionCoefficient(reservoir_,liq,water,salt)<<std::endl;
  if(supply_!="DistributedReservoir")DUNE_THROW(Dune::InvalidStateException,"Cylinder requires registered distributed supply; 2D slit is not a 3D aperture");
  std::cout<<"FIXED_HYDRAULICS enabled="<<this->spatialParams().fixedHydraulics()
   <<" salt_conserved=true temperature_mode="<<(NONISOTHERMAL?"nonisothermal":"isothermal")
   <<" solid_inventory_not_geometric_when_fixed=true"<<std::endl;
  permeability_.resize(gg->numDofs());
  diagnosticVelocity_.resize(gg->numDofs());dofIds_.resize(gg->numDofs());
  for(std::size_t i=0;i<dofIds_.size();++i)dofIds_[i]=i;
  activityWeights_.assign(gg->numDofs(),1.);
  std::cout<<"ACTIVITY_EVAPORATION enabled="<<activityMode_<<" relative_vapor_pressure="<<activityRH_
   <<" model=Pitzer_298K lag=previous_accepted_solution normalization=top_face_area"<<std::endl;
 }
 const std::string& name()const{return name_;}
 Scalar preDuration()const{return pre_;}
 void setTimeLoop(std::shared_ptr<TimeLoopBase<Scalar>> p){clock_=std::move(p);}
 Scalar startTime()const{return clock_?clock_->time():0;}
 Scalar stepSize()const{return clock_?clock_->timeStepSize():0;}
 std::vector<double> forcingEvents()const{auto v=series_.events();for(auto& t:v)t+=pre_;v.push_back(pre_);return v;}
 Scalar waterFlux()const {
  const auto a=startTime()-pre_,b=a+stepSize();if(stepSize()<=0||b<=0)return 0;
  if(seriesMode_)return getParam<Scalar>("Revision.WaterFluxAreaCorrection",1.)*series_.integral(std::max(Scalar(0),a),b)/stepSize();
  return constantWater_*(b-std::max(Scalar(0),a))/stepSize();
 }
 // Freeze normalized weights for one attempted step (including Newton retries).
 // This explicit lag avoids omitting a nonlocal normalization derivative in the
 // local Jacobian. The same weights are used in the solve and accepted budget.
 template<class GV>void prepareEvaporation(const SV& x,const GV& gv){
  if(!activityMode_)return;
  topDofs_.clear();topAreas_.clear();topAw_.clear();topMolality_.clear();topC_.clear();topX_.clear();
  activitySourceTime_=startTime();
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bind(e);
   auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);
   for(const auto& face:scvfs(fv))if(face.boundary()&&face.ipGlobal()[1]>this->gridGeometry().bBoxMax()[1]-1e-9){
    const auto& v=ev[face.insideScvIdx()];
    const auto m=v.moleFraction(liq,salt)/(v.moleFraction(liq,water)*FS::molarMass(water));
    topDofs_.push_back(fv.scv(face.insideScvIdx()).dofIndex());
    topAreas_.push_back(face.area()*v.extrusionFactor());
    topAw_.push_back(HeterogeneityRevision::naclWaterActivity(m,FS::molarMass(water)));
    topMolality_.push_back(m);topC_.push_back(v.moleFraction(liq,salt)*v.molarDensity(liq)/1000);
    topX_.push_back(face.ipGlobal()[0]);
   }
  }
  const auto weights=HeterogeneityRevision::normalizedEvaporationWeights(topAw_,topAreas_,activityRH_);
  for(std::size_t i=0;i<topDofs_.size();++i)activityWeights_[topDofs_[i]]=weights[i];
 }
 BoundaryTypes boundaryTypes(const Elem&,const Face&)const{BoundaryTypes t;t.setAllNeumann();return t;}
 PV initial(const Elem& e)const {
  PV p(0);p.setState(Ind::firstPhaseOnly);
  p[Ind::pressureIdx]=patm_+rhoRes_*9.81*(level_-e.geometry().center()[1]);
  p[Ind::switchIdx]=reservoir_.moleFraction(liq,air);p[salt]=reservoir_.moleFraction(liq,salt);p[solidEq]=getParam<Scalar>("Revision.TestInitialSolidVolumeFraction",0.);
  p[salt]=getParam<Scalar>("Revision.TestInitialSaltMoleFraction",p[salt]);
  const auto sg=getParam<Scalar>("Revision.TestInitialGasSaturation",0.);
  if(sg>0){p.setState(Ind::bothPhases);p[Ind::switchIdx]=sg;}
#if NONISOTHERMAL
  p[Ind::energyEqIdx]=temperature_;
#endif
  return p;
 }
 NumEqVector neumann(const Elem&,const FV& fv,const EV& ev,const FC&,const Face& face)const {
  NumEqVector q(0);if(getParam<bool>("Revision.ClosedReactionTest",false))return q;const auto& pos=face.ipGlobal();const auto& v=ev[face.insideScvIdx()];
  const auto& min=this->gridGeometry().bBoxMin();const auto& max=this->gridGeometry().bBoxMax();
  bool top=pos[1]>max[1]-1e-9,bottom=pos[1]<min[1]+1e-9;
  if(top){
   auto multiplier=activityMode_?activityWeights_[fv.scv(face.insideScvIdx()).dofIndex()]
    :(pos[0]<split_?coarseWaterMultiplier_:fineWaterMultiplier_);
   auto waterMassFlux=filmMode_?filmWaterFlux_(v):waterFlux()*multiplier;
   q[water]=waterMassFlux/FS::molarMass(water);
   // Prescribed water loss is the total water-component flux. Vent air
   // separately, as in the original model; do not add water advection twice.
   if(startTime()+stepSize()>pre_){
    const auto distance=(pos-fv.scv(face.insideScvIdx()).center()).two_norm();
    const auto gasDriving=v.pressure(gas)-patm_;
    const auto ambientAir=1-relativeHumidity_*Components::H2O<Scalar>::vaporPressure(temperature_)/patm_;
    q[air]=gasDriving/distance*v.mobility(gas)*v.permeability()*v.molarDensity(gas)
     *(gasDriving>0?v.moleFraction(gas,air):ambientAir);
   }
#if NONISOTHERMAL
   q[Ind::energyEqIdx]=Components::H2O<Scalar>::gasEnthalpy(v.temperature(),patm_)*waterMassFlux
    +Components::Air<Scalar>::gasThermalConductivity((v.temperature()+temperature_)/2,patm_)*(v.temperature()-temperature_)/filmDelta_
    +Components::Air<Scalar>::gasEnthalpy(q[air]>0?v.temperature():temperature_,patm_)*q[air]*FS::molarMass(air);
#endif
  }
  if(bottom){
   Scalar active=1;
   if(supply_=="CentralAperture"){
    auto half=face.area()/2,mid=(min[0]+max[0])/2;
    active=std::max(Scalar(0),std::min(pos[0]+half,mid+inlet_/2)-std::max(pos[0]-half,mid-inlet_/2))/face.area();
   }
   const auto center=fv.scv(face.insideScvIdx()).center();auto dist=(pos-center).two_norm();
   auto pExt=patm_+rhoRes_*9.81*(level_-pos[1]);
   // Upwinding follows the hydraulic potential including gravity, not pressure alone.
   auto rhoFace=(rhoRes_+v.density(liq))/2;
   auto driving=v.pressure(liq)-pExt+rhoFace*9.81*(center[1]-pos[1]);
   bool reservoirDonor=driving<0;
   auto mu=reservoirDonor?FS::viscosity(reservoir_,liq):v.viscosity(liq);
   auto kr=v.mobility(liq)*v.viscosity(liq);
   auto rTotal=resistance_+mu*dist/(v.permeability()*std::max(kr,Scalar(1e-15)));
   auto qVolume=active*driving/rTotal;
   for(int k=0;k<3;++k)q[k]=HeterogeneityRevision::donorComponentFlux(qVolume,molarRes_,reservoir_.moleFraction(liq,k),v.molarDensity(liq),v.moleFraction(liq,k));
#if NONISOTHERMAL
   q[Ind::energyEqIdx]+=qVolume<0?qVolume*rhoRes_*FS::enthalpy(reservoir_,liq):qVolume*v.density(liq)*v.enthalpy(liq);
#endif
  }
#if NONISOTHERMAL
  const bool side=!top&&!bottom;
  if(bottom||side)q[Ind::energyEqIdx]+=wallK_*(v.temperature()-temperature_)/wallD_;
#endif
  return q;
 }
 NumEqVector source(const Elem& e,const FV&,const EV& ev,const typename FV::SubControlVolume& scv)const {
  NumEqVector s(0);if(stepSize()<=0)return s;const auto& v=ev[scv];
  // Diagnostic-only gate: exercise the real invalid-trial guard and Newton retry.
  const auto rejectAbove=getParam<Scalar>("Revision.TestRejectDtAbove",-1);
  if(rejectAbove>0 && stepSize()>rejectAbove)FS::waterActivityFromFractions(.1,0.);
  if(equilibriumPrecipitation_){
   const auto ns=v.solidVolumeFraction(0)*v.solidComponentMolarDensity(0);
   const auto mSat=HeterogeneityRevision::saturationMolality(this->spatialParams().solubilityLimit(),FS::molarMass(salt));
   const auto gap=v.porosity()*v.saturation(liq)*v.molarDensity(liq)*(mSat*FS::molarMass(water)*v.moleFraction(liq,water)-v.moleFraction(liq,salt));
   // Salt equation stores dissolved + solid; the solid row is algebraic NCP.
   s[solidEq]=-HeterogeneityRevision::precipitationComplementarity(ns,gap)/stepSize();
   return s;
  }
  auto w=this->spatialParams().solubilityLimit(),mw=FS::molarMass(water),ms=FS::molarMass(salt);
  auto xmax=mw*w/(ms+(mw-ms)*w);
  auto rate=v.porosity()*v.saturation(liq)*v.molarDensity(liq)*(v.moleFraction(liq,salt)-xmax)/stepSize();
  rate=std::max(rate,-v.solidVolumeFraction(0)*v.solidComponentMolarDensity(0)/stepSize());
  if(v.solidVolumeFraction(0)>=this->spatialParams().referencePorosity(e,scv)-1e-5&&rate>0)rate=0;
  s[salt]=-rate;s[solidEq]=rate;return s;
 }
 template<class GV>Audit audit(const SV& x,const GV& gv)const {
  Audit a;
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);
   auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
   for(const auto& scv:scvs(fv)){
    const auto& v=ev[scv];auto volume=scv.volume()*v.extrusionFactor();
    if(this->spatialParams().fixedHydraulics()){
     const auto phi0=this->spatialParams().referencePorosity(e,scv);
     const auto k0=getParam<Scalar>(scv.center()[0]<=split_?"SpatialParams.CoarsePermeability":"SpatialParams.FinePermeability");
     if(v.porosity()!=phi0||v.permeability()!=k0)
      DUNE_THROW(Dune::InvalidStateException,"Fixed hydraulic phi/K changed in an accepted state");
    }
    for(int ph=0;ph<2;++ph){
     Scalar sum=0;
     if(v.saturation(ph)>1e-12&&(!std::isfinite(v.density(ph))||v.density(ph)<=0||!std::isfinite(v.molarDensity(ph))))DUNE_THROW(Dune::InvalidStateException,"Invalid phase density");
     for(int k=0;k<3;++k){
     auto frac=v.moleFraction(ph,k);
     if(!std::isfinite(frac)||frac<-1e-9||frac>1+1e-9)DUNE_THROW(Dune::InvalidStateException,"Nonphysical component fraction");
     sum+=frac;a.n[k]+=volume*v.porosity()*v.saturation(ph)*v.molarDensity(ph)*frac;
     }
     if(v.saturation(ph)>1e-12&&std::abs(sum-1)>1e-8)DUNE_THROW(Dune::InvalidStateException,"Active phase fractions do not sum to one");
    }
    auto nd=volume*v.porosity()*v.saturation(liq)*v.molarDensity(liq)*v.moleFraction(liq,salt);
    auto ns=volume*v.solidVolumeFraction(0)*v.solidComponentMolarDensity(0);
    a.dissolved+=nd;a.solid+=ns;(scv.center()[0]<split_?a.coarse:a.fine)+=nd+ns;
    (scv.center()[0]<split_?a.coarseSolid:a.fineSolid)+=ns;
    const auto molality=v.moleFraction(liq,salt)/(FS::molarMass(water)*v.moleFraction(liq,water));
    const auto msat=HeterogeneityRevision::saturationMolality(this->spatialParams().solubilityLimit(),FS::molarMass(salt));
    const auto gap=volume*v.porosity()*v.saturation(liq)*v.molarDensity(liq)*(msat*FS::molarMass(water)*v.moleFraction(liq,water)-v.moleFraction(liq,salt));
    a.mmax=std::max(a.mmax,double(molality));a.solidmin=std::min(a.solidmin,double(v.solidVolumeFraction(0)));
    a.ncpmax=std::max(a.ncpmax,std::abs(std::min(ns,gap))/std::max(1e-15,std::abs(nd+ns)));
    a.smin=std::min(a.smin,double(v.saturation(liq)));a.pmin=std::min(a.pmin,double(v.porosity()));
    a.precip=std::max(a.precip,double(v.solidVolumeFraction(0)));a.cmax=std::max(a.cmax,double(v.molarDensity(liq)*v.moleFraction(liq,salt)/1000));
#if NONISOTHERMAL
    NumEqVector storage(0);
    for(int ph=0;ph<2;++ph)EnergyLocalResidual<TypeTag>::fluidPhaseStorage(storage,scv,v,ph);
    EnergyLocalResidual<TypeTag>::solidPhaseStorage(storage,scv,v);
    a.energy+=volume*storage[Ind::energyEqIdx];
    a.tmin=std::min(a.tmin,double(v.temperature()));a.tmax=std::max(a.tmax,double(v.temperature()));
#endif
    if(!std::isfinite(v.porosity())||!std::isfinite(v.temperature())||!std::isfinite(v.pressure(liq))||v.porosity()<=0||v.saturation(liq)<-1e-9||v.saturation(liq)>1+1e-9||v.solidVolumeFraction(0)<-1e-10)DUNE_THROW(Dune::InvalidStateException,"Nonphysical pore/saturation state");
   }
   for(const auto& face:scvfs(fv)){
    if(face.boundary()){
     auto q=neumann(e,fv,ev,fc,face);auto factor=face.area()*ev[face.insideScvIdx()].extrusionFactor();
     for(int k=0;k<3;++k)a.out[k]+=q[k]*factor;
#if NONISOTHERMAL
     a.energyOut+=q[Ind::energyEqIdx]*factor;
#endif
     if(face.ipGlobal()[1]>this->gridGeometry().bBoxMax()[1]-1e-9)a.topWater[face.ipGlobal()[0]<split_?0:1]+=q[water]*factor;
     if(face.ipGlobal()[1]<this->gridGeometry().bBoxMin()[1]+1e-9){(face.ipGlobal()[0]<split_?a.bottomCoarse:a.bottomFine)+=q[salt]*factor;for(int k=0;k<3;++k)a.bottomOut[k]+=q[k]*factor;}
     if(filmMode_&&face.ipGlobal()[1]>this->gridGeometry().bBoxMax()[1]-1e-9){
      const auto& v=ev[face.insideScvIdx()];const auto pos=face.ipGlobal();
      const auto xs=v.moleFraction(liq,salt),xw=v.moleFraction(liq,water),aw=FS::waterActivity(v.fluidState());
      a.topAir+=q[air]*factor;
      a.filmFaces.push_back({double(pos[0]),double(pos[1]),double(pos[2]),double(factor),double(xs/(xw*FS::molarMass(water))),double(xs*v.molarDensity(liq)/1000),double(aw),double(aw*filmPsat_/patm_),double(v.moleFraction(gas,water)),double(v.pressure(gas)),double(v.saturation(liq)),double(q[water]*FS::molarMass(water)),double(aw*filmPsat_),double(v.moleFraction(gas,water)*v.pressure(gas))});
     }
    }
    else if(std::abs(face.ipGlobal()[0]-split_)<1e-9&&fv.scv(face.insideScvIdx()).center()[0]<split_){
     FluxVars flux;flux.init(*this,e,fv,ev,face,fc);
     for(int ph=0;ph<2;++ph){
      auto up=[ph](const auto& v){return v.molarDensity(ph)*v.moleFraction(ph,salt)*v.mobility(ph);};
      a.interfaceAdv+=flux.advectiveFlux(ph,up);auto d=flux.molecularDiffusionFlux(ph);
      if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged)a.interfaceDiff+=d[salt]/FS::molarMass(salt);
      else a.interfaceDiff+=d[salt];
     }
    }
   }
  }
  a.n[salt]+=a.solid;return a;
 }
 void initializeBudget(const Audit& a){initial_=a.n;initialParts_={a.coarse,a.fine};
#if NONISOTHERMAL
  initialEnergy_=a.energy;
#endif
 }
 void record(const Audit& a,Scalar time,Scalar dt){
  if(!mineralCsv_.is_open()){mineralCsv_.open("mineral_budget.csv");mineralCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s,salt_dissolved_mol,salt_solid_mol,coarse_solid_mol,fine_solid_mol,max_molality,min_solid_vf,max_relative_complementarity_residual\n";}
  mineralCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.dissolved<<','<<a.solid<<','<<a.coarseSolid<<','<<a.fineSolid<<','<<a.mmax<<','<<a.solidmin<<','<<a.ncpmax<<'\n';mineralCsv_.flush();
  if(time>0&&equilibriumPrecipitation_&&a.ncpmax>1e-6)DUNE_THROW(Dune::InvalidStateException,"Accepted step violates mineral complementarity");
  if(activityMode_){
   if(!activityCsv_.is_open()){
    activityCsv_.open("local_evaporation.csv");activityCsv_<<std::setprecision(17);
    activityCsv_<<"accepted_time_s,evaporation_time_h,dt_s,source_time_s,x_m,face_area_m2_per_m,molality_mol_kg_water,source_C_mol_L,water_activity,multiplier,water_flux_kg_m2_s\n";
   }
   for(std::size_t i=0;i<topDofs_.size();++i){
    auto w=activityWeights_[topDofs_[i]];
    activityCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<activitySourceTime_<<','<<topX_[i]<<','<<topAreas_[i]<<','<<topMolality_[i]<<','<<topC_[i]<<','<<topAw_[i]<<','<<w<<','<<waterFlux()*w<<'\n';
   }
   activityCsv_.flush();
  }
  if(!csv_.is_open()){
   csv_.open("budget.csv");csv_<<std::setprecision(17);
   csv_<<"time_s,evaporation_time_h,dt_s,water_mol,air_mol,salt_total_mol,salt_dissolved_mol,salt_solid_mol,coarse_salt_mol,fine_salt_mol,water_boundary_out_mol_s,salt_boundary_out_mol_s,cumulative_water_out_mol,cumulative_salt_out_mol,water_residual_mol,salt_residual_mol,interface_adv_mol_s,interface_diff_mol_s,cumulative_interface_adv_mol,cumulative_interface_diff_mol,coarse_bottom_salt_out_mol_s,fine_bottom_salt_out_mol_s,S_min,porosity_min,precip_vf_max,C_max_mol_L,coarse_residual_mol,fine_residual_mol,coarse_top_water_out_mol_s,fine_top_water_out_mol_s,cumulative_coarse_top_water_mol,cumulative_fine_top_water_mol\n";
  }
  for(int k=0;k<3;++k)cumulative_[k]+=dt*a.out[k];
  cumAdv_+=dt*a.interfaceAdv;cumDiff_+=dt*a.interfaceDiff;
  cumulativeBottom_[0]+=dt*a.bottomCoarse;cumulativeBottom_[1]+=dt*a.bottomFine;
  for(int i=0;i<2;++i)cumulativeTop_[i]+=dt*a.topWater[i];
  auto rw=a.n[water]-initial_[water]+cumulative_[water]-impulse_[water],rs=a.n[salt]-initial_[salt]+cumulative_[salt]-impulse_[salt];
  auto rc=a.coarse-initialParts_[0]+cumulativeBottom_[0]+cumAdv_+cumDiff_-impulseParts_[0];
  auto rf=a.fine-initialParts_[1]+cumulativeBottom_[1]-cumAdv_-cumDiff_-impulseParts_[1];
  if(filmMode_){
   for(int k=0;k<3;++k)filmBottomIntegral_[k]+=dt*a.bottomOut[k];
   if(!filmCsv_.is_open()){
    filmCsv_.open("film_budget.csv");filmCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s,top_water_mol_s,top_air_mol_s,bottom_water_out_mol_s,bottom_air_out_mol_s,bottom_salt_out_mol_s,cumulative_bottom_water_out_mol,cumulative_bottom_air_out_mol,cumulative_bottom_salt_out_mol,cumulative_reservoir_loss_g,cumulative_top_water_g,sample_water_g,water_residual_mol,salt_residual_mol\n";
    filmFaceCsv_.open("film_faces.csv");filmFaceCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s,x_m,y_m,z_m,area_m2,molality_mol_kg_water,C_mol_L,water_activity,surface_ywater_atm,cell_gas_ywater,cell_gas_pressure_Pa,S_liq,water_flux_kg_m2_s,equilibrium_pwater_Pa,cell_pwater_Pa\n";
   }
   Scalar reservoirLoss=0;for(int k=0;k<3;++k)reservoirLoss-=filmBottomIntegral_[k]*FS::molarMass(k)*1000;
   filmCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.topWater[0]+a.topWater[1]<<','<<a.topAir;
   for(auto v:a.bottomOut)filmCsv_<<','<<v;
   for(auto v:filmBottomIntegral_)filmCsv_<<','<<v;
   filmCsv_<<','<<reservoirLoss<<','<<(cumulativeTop_[0]+cumulativeTop_[1])*FS::molarMass(water)*1000<<','<<a.n[water]*FS::molarMass(water)*1000<<','<<rw<<','<<rs<<'\n';filmCsv_.flush();
   for(const auto& f:a.filmFaces){filmFaceCsv_<<time<<','<<(time-pre_)/3600<<','<<dt;for(auto v:f)filmFaceCsv_<<','<<v;filmFaceCsv_<<'\n';}filmFaceCsv_.flush();
  }
#if NONISOTHERMAL
  cumulativeEnergyOut_+=dt*a.energyOut;
  const auto energyResidual=a.energy-initialEnergy_+cumulativeEnergyOut_;
  if(!thermalCsv_.is_open()){
   thermalCsv_.open("thermal_budget.csv");thermalCsv_<<std::setprecision(17)
    <<"time_s,evaporation_time_h,dt_s,energy_J,energy_boundary_out_W,cumulative_energy_out_J,energy_residual_J,T_min_K,T_max_K\n";
  }
  thermalCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.energy<<','<<a.energyOut<<','<<cumulativeEnergyOut_<<','<<energyResidual<<','<<a.tmin<<','<<a.tmax<<'\n';thermalCsv_.flush();
  const auto eTol=getParam<Scalar>("Revision.MaxEnergyBudgetRelativeResidual",1e-6);
  if(std::abs(energyResidual)>eTol*std::max(std::abs(initialEnergy_),Scalar(1)))
   DUNE_THROW(Dune::InvalidStateException,"Energy budget residual exceeds registered gate");
#endif
  csv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.n[water]<<','<<a.n[air]<<','<<a.n[salt]<<','<<a.dissolved<<','<<a.solid<<','<<a.coarse<<','<<a.fine<<','<<a.out[water]<<','<<a.out[salt]<<','<<cumulative_[water]<<','<<cumulative_[salt]<<','<<rw<<','<<rs<<','<<a.interfaceAdv<<','<<a.interfaceDiff<<','<<cumAdv_<<','<<cumDiff_<<','<<a.bottomCoarse<<','<<a.bottomFine<<','<<a.smin<<','<<a.pmin<<','<<a.precip<<','<<a.cmax<<','<<rc<<','<<rf<<','<<a.topWater[0]<<','<<a.topWater[1]<<','<<cumulativeTop_[0]<<','<<cumulativeTop_[1]<<'\n';csv_.flush();
  auto tol=getParam<Scalar>("Revision.MaxBudgetRelativeResidual",.001);
  if(std::abs(rw)>tol*initial_[water]||std::abs(rs)>tol*initial_[salt])DUNE_THROW(Dune::InvalidStateException,"Budget residual exceeds registered gate");
 }
 template<class GV>bool seed(SV& x,GV& gv){
  if(seeded_||sigma_<=0)return false;
  seeded_=true;auto before=audit(x,gv);
  std::mt19937 generator(getParam<unsigned>("Revision.RandomSeed",1));std::normal_distribution<Scalar> normal(0,sigma_);
  std::vector<Scalar> noise(x.size());
  // Fixed physical-space perturbation, independent of DOF ordering.
  // Not inferred from MRI. Wavelengths and amplitude are frozen diagnostics.
  std::uniform_real_distribution<Scalar> phase(0.,2*std::acos(-1.));
  std::array<Scalar,6> phases;for(auto& p:phases)p=phase(generator);
  const std::array<std::array<double,3>,6> wavelengths={{{.012,.018,.010},{.020,.014,.016},{.008,.022,.018},{.016,.010,.024},{.024,.016,.012},{.010,.024,.020}}};
  Scalar sum=0,vol=0,square=0;
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bindElement(e);
   for(const auto& scv:scvs(fv)){
    const auto p=scv.center();Scalar value=0;
    for(int j=0;j<6;++j)value+=std::sin(2*std::acos(-1.)*((p[0]-.025)/wavelengths[j][0]+p[1]/wavelengths[j][1]+p[2]/wavelengths[j][2])+phases[j]);
    noise[scv.dofIndex()]=value;sum+=value*scv.volume();square+=value*value*scv.volume();vol+=scv.volume();
   }
  }
  const auto mean=sum/vol,rms=std::sqrt(square/vol-mean*mean);
  for(auto& v:noise)v=sigma_*(v-mean)/rms;
  auto candidate=x;
  auto total=[&](Scalar shift){for(std::size_t i=0;i<x.size();++i){candidate[i]=x[i];candidate[i][salt]+=noise[i]-shift;}gv.update(candidate);return audit(candidate,gv).n[salt];};
  Scalar left=-10*sigma_,right=10*sigma_;
  for(int i=0;i<38;++i){auto mid=(left+right)/2;if(total(mid)>before.n[salt])left=mid;else right=mid;}
  total((left+right)/2);x=candidate;gv.update(x);auto after=audit(x,gv);
  std::ofstream out("seed_event.json");out<<std::setprecision(17)<<"{\"time_s\":"<<startTime()<<",\"salt_moles_before\":"<<before.n[salt]<<",\"salt_moles_after\":"<<after.n[salt]<<",\"component_impulses_mol\":[";
  for(int k=0;k<3;++k){impulse_[k]+=after.n[k]-before.n[k];out<<(k?",":"")<<after.n[k]-before.n[k];}
  impulseParts_[0]+=after.coarse-before.coarse;impulseParts_[1]+=after.fine-before.fine;
  out<<"],\"partition_impulses_mol\":["<<impulseParts_[0]<<','<<impulseParts_[1]<<"]}\n";return true;
 }
 template<class Solution>void updateVtkOutput(const Solution& x){
  for(const auto& e:elements(this->gridGeometry().gridView())){auto fv=localView(this->gridGeometry());fv.bindElement(e);auto es=elementSolution(e,x,this->gridGeometry());
   for(const auto& scv:scvs(fv)){VV v;v.update(es,*this,e,scv);permeability_[scv.dofIndex()]=v.permeability();}}
 }
 const std::vector<Scalar>& getPermeability()const{return permeability_;}
 const auto& getDiagnosticVelocity()const{return diagnosticVelocity_;}
 const auto& getDofIds()const{return dofIds_;}
 template<class GV>void updateDiagnosticVelocity(const SV& x,const GV& gv){
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bind(e);
   auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);
   auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
   Dune::FieldMatrix<Scalar,3,3> a(0.);Dune::FieldVector<Scalar,3> b(0.),velocity(0.);
   for(const auto& f:scvfs(fv))if(!f.boundary()){
    FluxVars flux;flux.init(*this,e,fv,ev,f,fc);
    const auto q=flux.advectiveFlux(liq,[](const auto& v){return v.mobility(liq);})/(f.area()*ev[f.insideScvIdx()].extrusionFactor());
    const auto n=f.unitOuterNormal();
    for(int i=0;i<3;++i){b[i]+=f.area()*q*n[i];for(int j=0;j<3;++j)a[i][j]+=f.area()*n[i]*n[j];}
   }
   a.solve(velocity,b);diagnosticVelocity_[this->gridGeometry().elementMapper().index(e)]=velocity;
  }
 }
 bool equilibriumPrecipitation() const { return equilibriumPrecipitation_; }
private:
 const bool equilibriumPrecipitation_=getParam<bool>("Revision.EquilibriumPrecipitation",false);
 Scalar gasWaterMassFraction_(Scalar y)const{return FS::molarMass(water)*y/(FS::molarMass(water)*y+FS::molarMass(air)*(1-y));}
 Scalar filmWaterFlux_(const VV& v)const{
  const auto a=startTime()-pre_,b=a+stepSize();if(stepSize()<=0||b<=0)return 0;
  const auto surfaceTemperature=v.temperature();
  const auto surfacePsat=Components::H2O<Scalar>::vaporPressure(surfaceTemperature);
  const auto aw=FS::waterActivity(v.fluidState()),ys=aw*surfacePsat/patm_;
  if(!(ys>=0&&ys<1))DUNE_THROW(Dune::InvalidStateException,"Invalid film interfacial vapor state");
  const auto active=(b-std::max(Scalar(0),a))/stepSize();
  // Signed flux permits condensation; no normalization to observed total loss.
  const auto filmTemperature=(surfaceTemperature+temperature_)/2;
  State film;for(int ph=0;ph<2;++ph){film.setTemperature(ph,filmTemperature);film.setPressure(ph,patm_);film.setSaturation(ph,ph==gas?1:0);for(int k=0;k<3;++k)film.setMoleFraction(ph,k,0);}
  const auto yFilm=(ys+filmYRef_)/2;
  film.setMoleFraction(gas,water,yFilm);film.setMoleFraction(gas,air,1-yFilm);
  const auto rhoFilm=FS::density(film,gas),dFilm=FS::binaryDiffusionCoefficient(film,gas,water,air);
  return active*getParam<Scalar>("Revision.WaterFluxAreaCorrection",1.)*rhoFilm*dFilm/filmDelta_*(gasWaterMassFraction_(ys)-filmXRef_);
 }
 std::ofstream mineralCsv_;
 State reservoirState_(Scalar xs)const {
  State s;for(int ph=0;ph<2;++ph){s.setTemperature(ph,temperature_);s.setPressure(ph,patm_);s.setSaturation(ph,ph==liq?1:0);for(int k=0;k<3;++k)s.setMoleFraction(ph,k,0);}
  s.setMoleFraction(liq,salt,xs);s.setMoleFraction(liq,water,1-xs);s.setMoleFraction(gas,air,.98);s.setMoleFraction(gas,water,.02);
  Cache cache;for(int i=0;i<5;++i)UnifiedPhaseComposition<Scalar,FS>::both(s,cache,liq);return s;
 }
 std::shared_ptr<TimeLoopBase<Scalar>> clock_;State reservoir_;
 std::string name_,supply_;Scalar temperature_,patm_,level_,split_,pre_,sigma_,constantWater_,resistance_,inlet_,rhoRes_,molarRes_,coarseBL_,fineBL_,relativeHumidity_,wallK_,wallD_,coarseWaterMultiplier_,fineWaterMultiplier_;
 bool filmMode_=false;Scalar filmDelta_=0,filmRH_=0,filmPsat_=0,filmYRef_=0,filmXRef_=0,filmRhoRef_=0,filmD_=0;
 std::array<double,3> filmBottomIntegral_{};std::ofstream filmCsv_,filmFaceCsv_;
 bool seriesMode_=false,seeded_=false;HeterogeneityRevision::WaterFluxSeries series_;
 bool activityMode_=false;Scalar activityRH_=0,activitySourceTime_=0;
 std::vector<std::size_t> topDofs_;
 std::vector<double> topAreas_,topAw_,topMolality_,topC_,topX_,activityWeights_;
 std::ofstream activityCsv_;
 std::vector<Scalar> permeability_;std::array<double,3> initial_{},cumulative_{},impulse_{};
 std::vector<Dune::FieldVector<Scalar,3>> diagnosticVelocity_;
 std::vector<Scalar> dofIds_;
 std::array<double,2> initialParts_{},cumulativeBottom_{},impulseParts_{};
 std::array<double,2> cumulativeTop_{};
 double cumAdv_=0,cumDiff_=0;std::ofstream csv_;
#if NONISOTHERMAL
 double initialEnergy_=0,cumulativeEnergyOut_=0;std::ofstream thermalCsv_;
#endif
};
}
#endif
