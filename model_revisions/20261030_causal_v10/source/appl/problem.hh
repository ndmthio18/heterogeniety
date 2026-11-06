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
#include <dumux/material/constraintsolvers/misciblemultiphasecomposition.hh>
#include "revision_support.hh"
#include "water_activity.hh"
#include "phase_equilibrium.hh"
#include "causal_switches.hh"
#include <algorithm>
#include <string>
#include <vector>
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
  double smin=1,pmin=1,precip=0,cmax=0;
  // v10 causal diagnostics. Side 0=F36 coarse (x<=split), 1=W3 fine.
  // Interface fluxes are coarse->fine positive, [mode adv/diff][component][band].
  std::array<std::array<double,3>,2> sideN{},sideBoundaryOut{},sideBottomOut{},sideBottomOutPos{},sideBottomOutNeg{},sideTopOut{};
  std::array<std::array<double,5>,2> bandSalt{},bandDissolved{},bandWater{},bandLiquidVolume{};
  std::array<std::array<std::array<double,4>,3>,2> ifNet{},ifPos{},ifNeg{};
  std::array<double,4> ifVolNet{},ifVolPos{},ifVolNeg{};
  std::vector<double> planeAdv,planeAdvDown,planeDiff;
  std::size_t interfaceFaces=0;
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
  initCausal_(*gg);
  if(supply_!="DistributedReservoir")DUNE_THROW(Dune::InvalidStateException,"Cylinder requires registered distributed supply; 2D slit is not a 3D aperture");
  if(NONISOTHERMAL)DUNE_THROW(Dune::InvalidStateException,"Cylinder pilot is isothermal");
  permeability_.resize(gg->numDofs());
  diagnosticVelocity_.resize(gg->numDofs());dofIds_.resize(gg->numDofs());
  for(std::size_t i=0;i<dofIds_.size();++i)dofIds_[i]=i;
  activityWeights_.assign(gg->numDofs(),1.);
  std::cout<<"ACTIVITY_EVAPORATION enabled="<<activityMode_<<" relative_vapor_pressure="<<activityRH_
   <<" model=Pitzer_298K lag=previous_accepted_solution normalization=top_face_area"<<std::endl;
 }
 const std::string& name()const{return name_;}
 // v10: true only for interior faces between the two materials when the
 // interface exchange switch is off. Material is the spatial-parameter rule.
 template<class FVG,class F>bool interfaceExchangeBlocked(const FVG& fv,const F& f)const{
  if(interfaceExchange_||f.boundary())return false;
  return isCoarse_(fv.scv(f.insideScvIdx()).center())!=isCoarse_(fv.scv(f.outsideScvIdx()).center());
 }
 bool interfaceExchangeEnabled()const{return interfaceExchange_;}
 Scalar salinityBuoyancyScale()const{return lambda_;}
 template<class P>bool isCoarse(const P& p)const{return isCoarse_(p);}
 // Bottom hydraulic driving potential (Pa) with an explicit buoyancy scale; the
 // solver applies the configured scale in neumann().
 template<class V,class P>Scalar bottomDriving(const V& v,const P& pos,const P& center,Scalar lambda)const{
  auto pExt=patm_+rhoRes_*9.81*(level_-pos[1]);
  auto rhoFace=(rhoRes_+v.scaledBuoyancyDensity(liq,lambda))/2;
  return v.pressure(liq)-pExt+rhoFace*9.81*(center[1]-pos[1]);
 }
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
  p[Ind::switchIdx]=reservoir_.moleFraction(liq,air);p[salt]=reservoir_.moleFraction(liq,salt);p[solidEq]=0;
#if NONISOTHERMAL
  p[Ind::energyEqIdx]=temperature_;
#endif
  return p;
 }
 NumEqVector neumann(const Elem&,const FV& fv,const EV& ev,const FC&,const Face& face)const {
  NumEqVector q(0);const auto& pos=face.ipGlobal();const auto& v=ev[face.insideScvIdx()];
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
   q[Ind::energyEqIdx]=Components::H2O<Scalar>::gasEnthalpy(temperature_,patm_)*waterMassFlux
    +Components::Air<Scalar>::gasThermalConductivity(temperature_,patm_)*(v.temperature()-temperature_)/(pos[0]<split_?coarseBL_:fineBL_)
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
   // v10: buoyancy density (exactly the actual density for lambda=1).
   auto rhoFace=(rhoRes_+v.buoyancyDensity(liq))/2;
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
  if(bottom||pos[0]<min[0]+1e-9||pos[0]>max[0]-1e-9)q[Ind::energyEqIdx]+=wallK_*(v.temperature()-temperature_)/wallD_;
#endif
  return q;
 }
 NumEqVector source(const Elem& e,const FV&,const EV& ev,const typename FV::SubControlVolume& scv)const {
  NumEqVector s(0);if(stepSize()<=0)return s;const auto& v=ev[scv];
  auto w=this->spatialParams().solubilityLimit(),mw=FS::molarMass(water),ms=FS::molarMass(salt);
  auto xmax=mw*w/(ms+(mw-ms)*w);
  auto rate=v.porosity()*v.saturation(liq)*v.molarDensity(liq)*(v.moleFraction(liq,salt)-xmax)/stepSize();
  rate=std::max(rate,-v.solidVolumeFraction(0)*v.solidComponentMolarDensity(0)/stepSize());
  if(v.solidVolumeFraction(0)>=this->spatialParams().referencePorosity(e,scv)-1e-5&&rate>0)rate=0;
  s[salt]=-rate;s[solidEq]=rate;return s;
 }
 template<class GV>Audit audit(const SV& x,const GV& gv,bool fluxes=true)const {
  Audit a;a.planeAdv.assign(2*planeY_.size(),0.);a.planeAdvDown=a.planeAdv;a.planeDiff=a.planeAdv;
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);
   auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
   for(const auto& scv:scvs(fv)){
    const auto& v=ev[scv];auto volume=scv.volume()*v.extrusionFactor();
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
    {const int side=cellSide_[scv.dofIndex()];
     for(int ph=0;ph<2;++ph)for(int k=0;k<3;++k)a.sideN[side][k]+=volume*v.porosity()*v.saturation(ph)*v.molarDensity(ph)*v.moleFraction(ph,k);
     a.sideN[side][salt]+=ns;
     const double liquidVolume=volume*v.porosity()*v.saturation(liq),liquidWater=liquidVolume*v.molarDensity(liq)*v.moleFraction(liq,water);
     for(int b=0;b<5;++b){const double w=cellBand_[scv.dofIndex()][b];if(w==0)continue;
      a.bandSalt[side][b]+=w*(nd+ns);a.bandDissolved[side][b]+=w*nd;a.bandWater[side][b]+=w*liquidWater;a.bandLiquidVolume[side][b]+=w*liquidVolume;}}
    a.smin=std::min(a.smin,double(v.saturation(liq)));a.pmin=std::min(a.pmin,double(v.porosity()));
    a.precip=std::max(a.precip,double(v.solidVolumeFraction(0)));a.cmax=std::max(a.cmax,double(v.molarDensity(liq)*v.moleFraction(liq,salt)/1000));
    if(!std::isfinite(v.porosity())||!std::isfinite(v.temperature())||!std::isfinite(v.pressure(liq))||v.porosity()<=0||v.saturation(liq)<-1e-9||v.saturation(liq)>1+1e-9||v.solidVolumeFraction(0)<-1e-10)DUNE_THROW(Dune::InvalidStateException,"Nonphysical pore/saturation state");
   }
   for(const auto& face:scvfs(fv)){
    if(face.boundary()){
     auto q=neumann(e,fv,ev,fc,face);auto factor=face.area()*ev[face.insideScvIdx()].extrusionFactor();
     for(int k=0;k<3;++k)a.out[k]+=q[k]*factor;
     {const int side=cellSide_[fv.scv(face.insideScvIdx()).dofIndex()];
      const bool isTop=face.ipGlobal()[1]>this->gridGeometry().bBoxMax()[1]-1e-9,isBottom=face.ipGlobal()[1]<this->gridGeometry().bBoxMin()[1]+1e-9;
      for(int k=0;k<3;++k){const double r=q[k]*factor;a.sideBoundaryOut[side][k]+=r;
       if(isTop)a.sideTopOut[side][k]+=r;
       if(isBottom){a.sideBottomOut[side][k]+=r;(r>0?a.sideBottomOutPos:a.sideBottomOutNeg)[side][k]+=r;}}}
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
    if(fluxes&&!face.boundary())causalInteriorFace_(a,e,fv,ev,fc,face);
   }
  }
  a.n[salt]+=a.solid;return a;
 }
 void initializeBudget(const Audit& a){initial_=a.n;initialParts_={a.coarse,a.fine};initialSide_=a.sideN;}
 void record(const Audit& a,Scalar time,Scalar dt){
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
  csv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.n[water]<<','<<a.n[air]<<','<<a.n[salt]<<','<<a.dissolved<<','<<a.solid<<','<<a.coarse<<','<<a.fine<<','<<a.out[water]<<','<<a.out[salt]<<','<<cumulative_[water]<<','<<cumulative_[salt]<<','<<rw<<','<<rs<<','<<a.interfaceAdv<<','<<a.interfaceDiff<<','<<cumAdv_<<','<<cumDiff_<<','<<a.bottomCoarse<<','<<a.bottomFine<<','<<a.smin<<','<<a.pmin<<','<<a.precip<<','<<a.cmax<<','<<rc<<','<<rf<<','<<a.topWater[0]<<','<<a.topWater[1]<<','<<cumulativeTop_[0]<<','<<cumulativeTop_[1]<<'\n';csv_.flush();
  const auto sideResidual=recordCausal_(a,time,dt);
  auto tol=getParam<Scalar>("Revision.MaxBudgetRelativeResidual",.001);
  if(std::abs(rw)>tol*initial_[water]||std::abs(rs)>tol*initial_[salt])DUNE_THROW(Dune::InvalidStateException,"Budget residual exceeds registered gate");
  for(int s=0;s<2;++s)if(std::abs(sideResidual[s][water])>tol*initialSide_[s][water]||std::abs(sideResidual[s][salt])>tol*initialSide_[s][salt])
   DUNE_THROW(Dune::InvalidStateException,"v10 side budget residual exceeds registered gate");
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
  auto total=[&](Scalar shift){for(std::size_t i=0;i<x.size();++i){candidate[i]=x[i];candidate[i][salt]+=noise[i]-shift;}gv.update(candidate);return audit(candidate,gv,false).n[salt];};
  Scalar left=-10*sigma_,right=10*sigma_;
  for(int i=0;i<38;++i){auto mid=(left+right)/2;if(total(mid)>before.n[salt])left=mid;else right=mid;}
  total((left+right)/2);x=candidate;gv.update(x);auto after=audit(x,gv);
  std::ofstream out("seed_event.json");out<<std::setprecision(17)<<"{\"time_s\":"<<startTime()<<",\"salt_moles_before\":"<<before.n[salt]<<",\"salt_moles_after\":"<<after.n[salt]<<",\"component_impulses_mol\":[";
  for(int k=0;k<3;++k){impulse_[k]+=after.n[k]-before.n[k];out<<(k?",":"")<<after.n[k]-before.n[k];}
  impulseParts_[0]+=after.coarse-before.coarse;impulseParts_[1]+=after.fine-before.fine;
  out<<"],\"partition_impulses_mol\":["<<impulseParts_[0]<<','<<impulseParts_[1]<<"]";
  // v10: per-side component and per-band salt impulses (same seed definition).
  out<<",\"side_component_impulses_mol\":[";
  for(int s=0;s<2;++s){out<<(s?",[":"[");for(int k=0;k<3;++k){sideImpulse_[s][k]+=after.sideN[s][k]-before.sideN[s][k];out<<(k?",":"")<<after.sideN[s][k]-before.sideN[s][k];}out<<"]";}
  out<<"],\"band_salt_impulses_mol\":[";
  for(int s=0;s<2;++s){out<<(s?",[":"[");for(int b=0;b<5;++b)out<<(b?",":"")<<after.bandSalt[s][b]-before.bandSalt[s][b];out<<"]";}
  out<<"]}\n";return true;
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
private:
 template<class P>bool isCoarse_(const P& p)const{return p[0]<=split_;}
 template<std::size_t N>static std::array<double,N> bandFractions_(const std::array<double,N+1>& edges,double lo,double hi){
  std::array<double,N> w{};for(std::size_t b=0;b<N;++b)w[b]=std::max(0.,std::min(hi,edges[b+1])-std::max(lo,edges[b]))/(hi-lo);return w;
 }
 std::size_t planeIndex_(double y)const{
  auto it=std::lower_bound(planeY_.begin(),planeY_.end(),y-1e-12);
  if(it==planeY_.end()||std::abs(*it-y)>1e-12)DUNE_THROW(Dune::InvalidStateException,"Horizontal face outside registered planes");
  return std::size_t(it-planeY_.begin());
 }
 void initCausal_(const GG& gg){
  interfaceExchange_=HeterogeneityCausal::Switches::interfaceExchange();lambda_=HeterogeneityCausal::Switches::buoyancyScale();
  HeterogeneityCausal::BuoyancyReference::set({{double(reservoir_.moleFraction(liq,0)),double(reservoir_.moleFraction(liq,1)),double(reservoir_.moleFraction(liq,2))}});
  top_=gg.bBoxMax()[1];cellSide_.assign(gg.numDofs(),0);cellBand_.assign(gg.numDofs(),{});
  std::vector<double> levels;std::size_t materialFaces=0,geometricFaces=0,mismatch=0,centresOnSplit=0;double area=0;
  for(const auto& e:elements(gg.gridView())){
   auto fv=localView(gg);fv.bind(e);const auto g=e.geometry();
   double lo=1e9,hi=-1e9;for(int i=0;i<g.corners();++i){lo=std::min(lo,double(g.corner(i)[1]));hi=std::max(hi,double(g.corner(i)[1]));}
   for(const auto& scv:scvs(fv)){
    cellSide_[scv.dofIndex()]=isCoarse_(scv.center())?0:1;cellBand_[scv.dofIndex()]=bandFractions_<5>(inventoryEdges_,top_-hi,top_-lo);
    if(std::abs(scv.center()[0]-split_)<1e-12)++centresOnSplit;
   }
   for(const auto& f:scvfs(fv)){
    if(f.boundary())continue;
    const bool a=isCoarse_(fv.scv(f.insideScvIdx()).center()),b=isCoarse_(fv.scv(f.outsideScvIdx()).center()),geo=std::abs(f.ipGlobal()[0]-split_)<1e-9;
    if(a&&!b){++materialFaces;area+=f.area();}
    if(geo&&fv.scv(f.insideScvIdx()).center()[0]<split_)++geometricFaces;
    if((a!=b)!=geo)++mismatch;
    if(f.unitOuterNormal()[1]<-.99)levels.push_back(f.ipGlobal()[1]);
   }
  }
  std::sort(levels.begin(),levels.end());
  for(auto y:levels)if(planeY_.empty()||y-planeY_.back()>1e-12)planeY_.push_back(y);
  if(mismatch||centresOnSplit||materialFaces!=geometricFaces||materialFaces==0)
   DUNE_THROW(Dune::InvalidStateException,"Material-interface faces do not coincide with the geometric split plane");
  interfaceFaces_=materialFaces;interfaceArea_=area;
  std::ofstream out("causal_switches.json");out<<std::setprecision(17)<<"{\"InterfaceExchangeEnabled\":"<<(interfaceExchange_?"true":"false")
   <<",\"SalinityBuoyancyScale\":"<<lambda_<<",\"reference_liquid_mole_fractions_water_air_NaCl\":["<<reservoir_.moleFraction(liq,0)<<','<<reservoir_.moleFraction(liq,1)<<','<<reservoir_.moleFraction(liq,2)
   <<"],\"reference_molarity_mol_L\":"<<reservoir_.moleFraction(liq,salt)*molarRes_/1000<<",\"reference_density_at_patm_T_kg_m3\":"<<rhoRes_
   <<",\"buoyancy_density\":\"liquid: rho_ref(p_liq,T,x_ref)+lambda*(rho-rho_ref); lambda=1 uses the upstream law and actual rho; gas phase actual density\""
   <<",\"interface_rule\":\"interior face with cells in different materials (x<=split coarse) has zero Darcy flux of both phases and zero Fickian flux of all components when disabled\""
   <<",\"interface_faces\":"<<interfaceFaces_<<",\"interface_area_m2\":"<<interfaceArea_<<",\"split_m\":"<<split_
   <<",\"side_convention\":\"0=F36 coarse x<=split, 1=W3 fine\",\"interface_sign\":\"positive coarse to fine\",\"inventory_band_edges_depth_m\":[";
  for(std::size_t i=0;i<inventoryEdges_.size();++i)out<<(i?",":"")<<inventoryEdges_[i];
  out<<"],\"interface_band_edges_depth_m\":[";for(std::size_t i=0;i<interfaceEdges_.size();++i)out<<(i?",":"")<<interfaceEdges_[i];
  out<<"],\"horizontal_plane_depths_m\":[";for(std::size_t i=0;i<planeY_.size();++i)out<<(i?",":"")<<top_-planeY_[i];out<<"]}\n";
  std::cout<<std::setprecision(17)<<"CAUSAL_SWITCHES interface_exchange="<<interfaceExchange_<<" salinity_buoyancy_scale="<<lambda_<<" interface_faces="<<interfaceFaces_<<" interface_area_m2="<<interfaceArea_<<" planes="<<planeY_.size()<<std::endl;
 }
 template<class EV_,class FC_>void causalInteriorFace_(Audit& a,const Elem& e,const FV& fv,const EV_& ev,const FC_& fc,const Face& face)const{
  const auto& inside=fv.scv(face.insideScvIdx());const auto& outside=fv.scv(face.outsideScvIdx());
  const bool inC=isCoarse_(inside.center()),outC=isCoarse_(outside.center()),across=inC&&!outC,plane=face.unitOuterNormal()[1]<-.99;
  if(!across&&!plane)return;
  FluxVars flux;flux.init(*this,e,fv,ev,face,fc);
  std::array<double,3> adv{},dif{};
  for(int ph=0;ph<2;++ph){
   const auto d=flux.molecularDiffusionFlux(ph);
   for(int k=0;k<3;++k){
    adv[k]+=flux.advectiveFlux(ph,[ph,k](const auto& v){return v.molarDensity(ph)*v.moleFraction(ph,k)*v.mobility(ph);});
    if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged)dif[k]+=d[k]/FS::molarMass(k);
    else dif[k]+=d[k];
   }
  }
  if(across){
   ++a.interfaceFaces;
   const double volume=flux.advectiveFlux(liq,[](const auto& v){return v.mobility(liq);});
   const auto g=fv.geometry(face);double lo=1e9,hi=-1e9;
   for(int i=0;i<g.corners();++i){lo=std::min(lo,double(g.corner(i)[1]));hi=std::max(hi,double(g.corner(i)[1]));}
   const auto w=bandFractions_<4>(interfaceEdges_,top_-hi,top_-lo);
   for(int b=0;b<4;++b){if(w[b]==0)continue;
    for(int m=0;m<2;++m)for(int k=0;k<3;++k){const double F=w[b]*(m?dif[k]:adv[k]);a.ifNet[m][k][b]+=F;(F>0?a.ifPos:a.ifNeg)[m][k][b]+=F;}
    const double F=w[b]*volume;a.ifVolNet[b]+=F;(F>0?a.ifVolPos:a.ifVolNeg)[b]+=F;
   }
  }
  if(plane){
   const std::size_t i=(inC?0:1)*planeY_.size()+planeIndex_(face.ipGlobal()[1]);
   a.planeAdv[i]+=adv[salt];a.planeAdvDown[i]+=std::max(0.,adv[salt]);a.planeDiff[i]+=dif[salt];
  }
 }
 std::array<std::array<double,3>,2> recordCausal_(const Audit& a,Scalar time,Scalar dt){
  static const char* side[2]={"F36","W3"};static const char* comp[3]={"water","air","salt"};static const char* mode[2]={"adv","diff"};
  static const char* inv[5]={"0_2","2_3","3_10","10_20","20_40"};static const char* ifb[4]={"0_2","2_10","10_20","20_40"};
  if(!causalCsv_.is_open()){
   causalCsv_.open("causal_budget.csv");causalCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s,interface_faces_evaluated";
   for(int s=0;s<2;++s){
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<'_'<<comp[k]<<"_mol";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_bottom_"<<comp[k]<<"_in_mol_s,"<<side[s]<<"_top_"<<comp[k]<<"_out_mol_s,"<<side[s]<<"_boundary_"<<comp[k]<<"_out_mol_s";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_cum_bottom_"<<comp[k]<<"_in_mol,"<<side[s]<<"_cum_bottom_"<<comp[k]<<"_gross_in_mol,"<<side[s]<<"_cum_bottom_"<<comp[k]<<"_gross_out_mol,"<<side[s]<<"_cum_top_"<<comp[k]<<"_out_mol,"<<side[s]<<"_cum_boundary_"<<comp[k]<<"_out_mol";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_residual_"<<comp[k]<<"_mol";
    for(int b=0;b<5;++b)causalCsv_<<','<<side[s]<<"_salt_mol_"<<inv[b]<<"mm,"<<side[s]<<"_dissolved_salt_mol_"<<inv[b]<<"mm,"<<side[s]<<"_liquid_water_mol_"<<inv[b]<<"mm,"<<side[s]<<"_liquid_volume_m3_"<<inv[b]<<"mm";
   }
   for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b){const auto n=std::string("if_")+mode[m]+"_"+comp[k]+"_"+ifb[b]+"mm";causalCsv_<<','<<n<<"_mol_s,"<<n<<"_cum_net_mol,"<<n<<"_cum_pos_mol,"<<n<<"_cum_neg_mol";}
   for(int b=0;b<4;++b){const auto n=std::string("if_liquid_volume_")+ifb[b]+"mm";causalCsv_<<','<<n<<"_m3_s,"<<n<<"_cum_net_m3,"<<n<<"_cum_pos_m3,"<<n<<"_cum_neg_m3";}
   causalCsv_<<'\n';
   planeCsv_.open("vertical_salt_flux.csv");planeCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s";
   for(int s=0;s<2;++s)for(std::size_t l=0;l<planeY_.size();++l){const auto d=std::to_string(std::lround((top_-planeY_[l])*1e7));
    planeCsv_<<','<<side[s]<<"_adv_down_net_mol_s_d"<<d<<','<<side[s]<<"_adv_down_gross_mol_s_d"<<d<<','<<side[s]<<"_diff_down_net_mol_s_d"<<d;}
   planeCsv_<<'\n';
  }
  for(int s=0;s<2;++s)for(int k=0;k<3;++k){
   cumSideBoundaryOut_[s][k]+=dt*a.sideBoundaryOut[s][k];cumSideBottomOut_[s][k]+=dt*a.sideBottomOut[s][k];cumSideTopOut_[s][k]+=dt*a.sideTopOut[s][k];
   cumSideBottomOutPos_[s][k]+=dt*a.sideBottomOutPos[s][k];cumSideBottomOutNeg_[s][k]+=dt*a.sideBottomOutNeg[s][k];
  }
  for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b){cumIfNet_[m][k][b]+=dt*a.ifNet[m][k][b];cumIfPos_[m][k][b]+=dt*a.ifPos[m][k][b];cumIfNeg_[m][k][b]+=dt*a.ifNeg[m][k][b];}
  for(int b=0;b<4;++b){cumIfVolNet_[b]+=dt*a.ifVolNet[b];cumIfVolPos_[b]+=dt*a.ifVolPos[b];cumIfVolNeg_[b]+=dt*a.ifVolNeg[b];}
  std::array<std::array<double,3>,2> residual{};
  for(int k=0;k<3;++k){double I=0;for(int m=0;m<2;++m)for(int b=0;b<4;++b)I+=cumIfNet_[m][k][b];
   for(int s=0;s<2;++s)residual[s][k]=a.sideN[s][k]-initialSide_[s][k]+cumSideBoundaryOut_[s][k]+(s==0?I:-I)-sideImpulse_[s][k];}
  causalCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.interfaceFaces;
  for(int s=0;s<2;++s){
   for(int k=0;k<3;++k)causalCsv_<<','<<a.sideN[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<-a.sideBottomOut[s][k]<<','<<a.sideTopOut[s][k]<<','<<a.sideBoundaryOut[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<-cumSideBottomOut_[s][k]<<','<<-cumSideBottomOutNeg_[s][k]<<','<<cumSideBottomOutPos_[s][k]<<','<<cumSideTopOut_[s][k]<<','<<cumSideBoundaryOut_[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<residual[s][k];
   for(int b=0;b<5;++b)causalCsv_<<','<<a.bandSalt[s][b]<<','<<a.bandDissolved[s][b]<<','<<a.bandWater[s][b]<<','<<a.bandLiquidVolume[s][b];
  }
  for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b)causalCsv_<<','<<a.ifNet[m][k][b]<<','<<cumIfNet_[m][k][b]<<','<<cumIfPos_[m][k][b]<<','<<cumIfNeg_[m][k][b];
  for(int b=0;b<4;++b)causalCsv_<<','<<a.ifVolNet[b]<<','<<cumIfVolNet_[b]<<','<<cumIfVolPos_[b]<<','<<cumIfVolNeg_[b];
  causalCsv_<<'\n';causalCsv_.flush();
  planeCsv_<<time<<','<<(time-pre_)/3600<<','<<dt;
  for(std::size_t i=0;i<a.planeAdv.size();++i)planeCsv_<<','<<a.planeAdv[i]<<','<<a.planeAdvDown[i]<<','<<a.planeDiff[i];
  planeCsv_<<'\n';planeCsv_.flush();
  return residual;
 }
 Scalar gasWaterMassFraction_(Scalar y)const{return FS::molarMass(water)*y/(FS::molarMass(water)*y+FS::molarMass(air)*(1-y));}
 Scalar filmWaterFlux_(const VV& v)const{
  const auto a=startTime()-pre_,b=a+stepSize();if(stepSize()<=0||b<=0)return 0;
  const auto aw=FS::waterActivity(v.fluidState()),ys=aw*filmPsat_/patm_;
  if(!(ys>=0&&ys<1))DUNE_THROW(Dune::InvalidStateException,"Invalid film interfacial vapor state");
  const auto active=(b-std::max(Scalar(0),a))/stepSize();
  // Signed flux permits condensation; no normalization to observed total loss.
  return active*getParam<Scalar>("Revision.WaterFluxAreaCorrection",1.)*filmRhoRef_*filmD_/filmDelta_*(gasWaterMassFraction_(ys)-filmXRef_);
 }
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
 // v10 causal state
 bool interfaceExchange_=true;Scalar lambda_=1;double top_=0,interfaceArea_=0;std::size_t interfaceFaces_=0;
 const std::array<double,6> inventoryEdges_{{0,.002,.003,.010,.020,.040}};
 const std::array<double,5> interfaceEdges_{{0,.002,.010,.020,.040}};
 std::vector<int> cellSide_;std::vector<std::array<double,5>> cellBand_;std::vector<double> planeY_;
 std::array<std::array<double,3>,2> initialSide_{},sideImpulse_{},cumSideBoundaryOut_{},cumSideBottomOut_{},cumSideTopOut_{},cumSideBottomOutPos_{},cumSideBottomOutNeg_{};
 std::array<std::array<std::array<double,4>,3>,2> cumIfNet_{},cumIfPos_{},cumIfNeg_{};
 std::array<double,4> cumIfVolNet_{},cumIfVolPos_{},cumIfVolNeg_{};
 std::ofstream causalCsv_,planeCsv_;
};
}
#endif
