#ifndef CYLINDER_UNIFIED_PHASE_EQUILIBRIUM_HH
#define CYLINDER_UNIFIED_PHASE_EQUILIBRIUM_HH
#include <cmath>
#include <dumux/material/binarycoefficients/h2o_air.hh>
#include <dumux/material/constraintsolvers/misciblemultiphasecomposition.hh>
#include <dumux/material/constraintsolvers/computefromreferencephase.hh>
namespace Dumux {
// Local replacement of composition calculations only. Density/viscosity and
// transport relations are inherited. Nonvolatile salt must remain in liquid.
template<class Scalar,class FS>struct UnifiedPhaseComposition {
 template<class State,class Cache>static void finish(State& s,Cache& cache){
  for(int ph=0;ph<2;++ph){
   cache.updatePhase(s,ph);
   for(int k=0;k<FS::numComponents;++k)s.setFugacityCoefficient(ph,k,FS::fugacityCoefficient(s,cache,ph,k));
   s.setDensity(ph,FS::density(s,cache,ph));s.setMolarDensity(ph,FS::molarDensity(s,cache,ph));
  }
 }
 template<class State,class Cache>static void both(State& s,Cache& cache,int known=0){
  if(!FS::unifiedWaterActivity()){MiscibleMultiPhaseComposition<Scalar,FS>::solve(s,cache,known);return;}
  const int l=FS::liquidPhaseIdx,g=FS::gasPhaseIdx,w=FS::H2OIdx,a=FS::AirIdx,z=FS::NaClIdx;
  if(known!=l)DUNE_THROW(Dune::InvalidStateException,"Unified NaCl equilibrium requires known liquid salt composition");
  const Scalar xs=s.moleFraction(l,z),pg=s.pressure(g),T=s.temperature(l);
  const auto H=BinaryCoeff::H2O_Air::henry(T),ps=FS::H2O::vaporPressure(T);
  if(xs<0||xs>=1||pg<=ps)DUNE_THROW(NumericalProblem,"Invalid trial brine/pressure state in Pitzer equilibrium");
  const auto alpha=pg/H,beta=ps/pg;
  Scalar xw=1-xs-alpha;
  for(int it=0;it<12;++it){
   const auto aw=FS::waterActivityFromFractions(xs,xw);
   const auto next=1-xs-alpha*(1-beta*aw);
   if(std::abs(next-xw)<1e-15){xw=next;break;}xw=next;
  }
  const auto yw=beta*FS::waterActivityFromFractions(xs,xw),ya=1-yw,xa=alpha*ya;
  xw=1-xs-xa;
  if(std::abs(yw-beta*FS::waterActivityFromFractions(xs,xw))>1e-12)
   DUNE_THROW(NumericalProblem,"Pitzer scalar composition solve did not converge");
  s.setMoleFraction(l,w,xw);s.setMoleFraction(l,a,xa);s.setMoleFraction(l,z,xs);
  s.setMoleFraction(g,w,yw);s.setMoleFraction(g,a,ya);s.setMoleFraction(g,z,0);
  finish(s,cache);
 }
 template<class State,class Cache>static void reference(State& s,Cache& cache,int ref){
  if(!FS::unifiedWaterActivity()){ComputeFromReferencePhase<Scalar,FS>::solve(s,cache,ref);return;}
  const int l=FS::liquidPhaseIdx,g=FS::gasPhaseIdx,w=FS::H2OIdx,a=FS::AirIdx,z=FS::NaClIdx;
  if(ref!=l)DUNE_THROW(Dune::InvalidStateException,"Unified nonvolatile-salt model requires liquid to remain present");
  const auto T=s.temperature(l),pg=s.pressure(g);
  const auto yw=FS::waterActivity(s)*FS::H2O::vaporPressure(T)/pg;
  const auto ya=BinaryCoeff::H2O_Air::henry(T)*s.moleFraction(l,a)/pg;
  // The absent gas is intentionally not normalized: its sum controls appearance.
  s.setMoleFraction(g,w,yw);s.setMoleFraction(g,a,ya);s.setMoleFraction(g,z,0);
  finish(s,cache);
 }
};
}
#endif
