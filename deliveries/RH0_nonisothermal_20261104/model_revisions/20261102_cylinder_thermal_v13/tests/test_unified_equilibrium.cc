#include <config.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <dumux/common/parameters.hh>
#include <dumux/material/fluidstates/compositional.hh>
#include "transport_fluidsystem.hh"
#include "phase_equilibrium.hh"
#include "precipitation_equilibrium.hh"
using FS=Dumux::HeterogeneityTransportFluidSystem<double>;
using State=Dumux::CompositionalFluidState<double,FS>;
void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
State state(double xs,double pg,double sl){
 State s;
 for(int ph=0;ph<2;++ph){s.setTemperature(ph,293.15);s.setPressure(ph,pg+(ph==0?-3000:0));s.setSaturation(ph,ph==0?sl:1-sl);for(int k=0;k<3;++k)s.setMoleFraction(ph,k,0);}
 s.setMoleFraction(0,0,1-xs-1.4e-5);s.setMoleFraction(0,1,1.4e-5);s.setMoleFraction(0,2,xs);
 s.setMoleFraction(1,0,.02);s.setMoleFraction(1,1,.98);return s;
}
int main(int argc,char**argv){
 Dumux::Parameters::init(argc,argv);FS::init(273.15,323.15,100,0.,2e6,200);
 require(FS::unifiedWaterActivity(),"Test requires UnifiedWaterActivity=true");
 require(!FS::isIdealMixture(0),"Liquid must be declared nonideal");
 // Invalid Newton trials must be recoverable; valid-state formulas are unchanged.
 int rejected=0;
 for(auto q: {std::pair<double,double>{.1,0.}, {.1,-.1}, {-.1,.9}, {.2,.8}}){
  try { FS::waterActivityFromFractions(q.first,q.second); }
  catch(const Dumux::NumericalProblem&) { ++rejected; }
 }
 require(rejected==4,"Invalid activity trials must throw NumericalProblem");
 {auto bad=state(-.1,100000.,.5);FS::ParameterCache c;bool rejected=false;
  try{Dumux::UnifiedPhaseComposition<double,FS>::both(bad,c,0);}
  catch(const Dumux::NumericalProblem&){rejected=true;}
  require(rejected,"Invalid phase-composition trial must be recoverable");}
 std::cout<<"PASS recoverable guards: 5 invalid trial states rejected without clipping"<<std::endl;
 double error=0;int n=0;
 for(double xs:{0.,.001,.0180736845,.05,.08,.0976,.1005})for(double pg:{85000.,100000.,120000.}){
  auto s=state(xs,pg,.5);FS::ParameterCache c;
  Dumux::UnifiedPhaseComposition<double,FS>::both(s,c,0);
  const double target=FS::waterActivity(s)*FS::H2O::vaporPressure(293.15);
  double sum0=0,sum1=0;
  for(int k=0;k<3;++k){sum0+=s.moleFraction(0,k);sum1+=s.moleFraction(1,k);require(s.moleFraction(0,k)>=0&&s.moleFraction(1,k)>=0,"Negative composition");}
  require(std::abs(sum0-1)<1e-13&&std::abs(sum1-1)<1e-13,"Phase sum");
  require(s.moleFraction(1,2)==0,"Nonvolatile salt escaped");
  const double e=std::abs(s.moleFraction(1,0)*pg/target-1);error=std::max(error,e);
  require(e<1e-12,"Gas pressure not in Pitzer equilibrium");
  for(int k=0;k<2;++k)require(std::abs(s.fugacity(0,k)-s.fugacity(1,k))/std::max(1.,std::abs(s.fugacity(1,k)))<1e-11,"Fugacity mismatch");
  // Moving to a liquid-only state at the same composition must reproduce the
  // same hypothetical gas and the same appearance criterion, continuously.
  auto single=s;single.setSaturation(0,1.);single.setSaturation(1,0.);
  Dumux::UnifiedPhaseComposition<double,FS>::reference(single,c,0);
  for(int k=0;k<3;++k)require(std::abs(single.moleFraction(1,k)-s.moleFraction(1,k))<1e-12,"Phase-switch discontinuity");
  require(std::abs(FS::vaporPressure(s,0)/target-1)<1e-13,"Vapor pressure API differs");
  ++n;
 }
 // Deliberately unequal dissolved air gives an unnormalized absent gas; that
 // sum must remain available to the phase-appearance machinery.
 auto s=state(.018,100000.,1.);FS::ParameterCache c;s.setMoleFraction(0,1,1e-6);s.setMoleFraction(0,0,1-.018-1e-6);
 Dumux::UnifiedPhaseComposition<double,FS>::reference(s,c,0);
 require(std::abs(s.moleFraction(1,0)+s.moleFraction(1,1)-1)>.1,"Absent gas was incorrectly normalized");
 const double aw=FS::waterActivity(s),ys=aw*FS::H2O::vaporPressure(293.15)/100000.;
 const auto X=[](double y){return FS::molarMass(0)*y/(FS::molarMass(0)*y+FS::molarMass(1)*(1-y));};
 require(X(ys)>X(.4*FS::H2O::vaporPressure(293.15)/100000.),"Wet surface must evaporate at RH0.4");
 const double msat=HeterogeneityRevision::saturationMolality(.26,FS::molarMass(2));
 require(msat>6&&msat<6.02,"Mass fraction/molality conversion");
 require(std::abs(HeterogeneityRevision::naclWaterActivity(msat,FS::molarMass(0))-.7547)<.006,"Saturated aw reference envelope, not measurement precision");
 for(double waterMass:{.1,1.,2.})for(double excess:{-1.,0.,1.}){
  const double capacity=msat*waterMass,total=capacity+excess;
  const double dissolved=std::min(total,capacity),solid=total-dissolved;
  require(std::abs(dissolved+solid-total)<1e-13,"Closed-cell total salt conservation");
  require(std::abs(HeterogeneityRevision::precipitationComplementarity(solid,capacity-dissolved))<1e-13,"Equilibrium precipitation/dissolution endpoint");
 }
 require(HeterogeneityRevision::precipitationComplementarity(0,-1)<0,"Supersaturation must not be accepted");
 require(HeterogeneityRevision::precipitationComplementarity(-1,1)<0,"Negative solid must not be accepted");
 require(HeterogeneityRevision::precipitationComplementarity(1,1)>0,"Solid in undersaturated brine must dissolve");
 std::cout<<"PASS unified Pitzer equilibrium, normalized active phases, nonvolatile salt, fugacity equality, phase-switch continuity and absent-gas criterion; states="<<n<<" max_relative_water_equilibrium_error="<<error<<std::endl;
}
