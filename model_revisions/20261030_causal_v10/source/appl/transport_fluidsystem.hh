#ifndef HETEROGENEITY_TRANSPORT_FLUIDSYSTEM_HH
#define HETEROGENEITY_TRANSPORT_FLUIDSYSTEM_HH
#include <dumux/common/parameters.hh>
#include <dumux/material/fluidsystems/brineair.hh>
#include "water_activity.hh"
namespace Dumux {
// A declared sensitivity of the liquid water/salt binary diffusivity only.
// Density, viscosity, dissolved-air diffusion and all gas coefficients retain
// the original fluid-system definitions. No dependency file is edited.
template<class Scalar>
class HeterogeneityTransportFluidSystem:public FluidSystems::BrineAir<Scalar,Components::H2O<Scalar>> {
 using Parent=FluidSystems::BrineAir<Scalar,Components::H2O<Scalar>>;
public:
 static bool unifiedWaterActivity(){static const bool value=getParam<bool>("Revision.UnifiedWaterActivity",false);return value;}
 static bool isIdealMixture(int phase){return unifiedWaterActivity()&&phase==Parent::liquidPhaseIdx?false:Parent::isIdealMixture(phase);}
 static Scalar waterActivityFromFractions(Scalar xs,Scalar xw){
  if(!(xw>0))DUNE_THROW(Dune::InvalidStateException,"Nonpositive liquid water fraction");
  return HeterogeneityRevision::naclWaterActivity(xs/(xw*Parent::molarMass(Parent::H2OIdx)),Parent::molarMass(Parent::H2OIdx));
 }
 template<class State>static Scalar waterActivity(const State& s){return waterActivityFromFractions(s.moleFraction(Parent::liquidPhaseIdx,Parent::NaClIdx),s.moleFraction(Parent::liquidPhaseIdx,Parent::H2OIdx));}
 template<class State>static Scalar fugacityCoefficient(const State& s,int phase,int comp){
  if(!unifiedWaterActivity()||phase!=Parent::liquidPhaseIdx||comp!=Parent::H2OIdx)return Parent::fugacityCoefficient(s,phase,comp);
  const auto xw=s.moleFraction(phase,comp);
  return Parent::H2O::vaporPressure(s.temperature(phase))*waterActivity(s)/(xw*s.pressure(phase));
 }
 template<class State,class Cache>static Scalar fugacityCoefficient(const State& s,const Cache&,int phase,int comp){return fugacityCoefficient(s,phase,comp);}
 template<class State>static Scalar vaporPressure(const State& s,int comp){
  if(unifiedWaterActivity()&&comp==Parent::H2OIdx)return Parent::H2O::vaporPressure(s.temperature(Parent::liquidPhaseIdx))*waterActivity(s);
  return Parent::vaporPressure(s,comp);
 }
 template<class State>
 static Scalar binaryDiffusionCoefficient(const State& state,int phase,int i,int j){
  auto value=Parent::binaryDiffusionCoefficient(state,phase,i,j);
  if(phase==Parent::liquidPhaseIdx&&((i==Parent::H2OIdx&&j==Parent::NaClIdx)||(j==Parent::H2OIdx&&i==Parent::NaClIdx))){
   const auto scale=getParam<Scalar>("Revision.SaltDiffusionScale",1.);
   if(!(scale>0))DUNE_THROW(Dune::InvalidStateException,"Salt diffusion scale must be positive");
   value*=scale;
  }
  return value;
 }
 template<class State,class Cache>
 static Scalar binaryDiffusionCoefficient(const State& state,const Cache&,int phase,int i,int j)
 {return binaryDiffusionCoefficient(state,phase,i,j);}
};
}
#endif
