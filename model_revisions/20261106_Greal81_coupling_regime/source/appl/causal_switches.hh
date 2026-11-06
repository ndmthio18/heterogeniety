#ifndef HETEROGENEITY_CAUSAL_SWITCHES_HH
#define HETEROGENEITY_CAUSAL_SWITCHES_HH
// Run-time switch values and the registered buoyancy reference composition.
// Definitions of the switches are documented in causal_flux.hh.
#include <array>
#include <dune/common/exceptions.hh>
#include <dumux/common/parameters.hh>
namespace HeterogeneityCausal {
struct Switches {
 static bool interfaceExchange(){static const bool v=Dumux::getParam<bool>("Revision.InterfaceExchangeEnabled",true);return v;}
 static double buoyancyScale(){
  static const double v=[]{
   auto l=Dumux::getParam<double>("Revision.SalinityBuoyancyScale",1.);
   if(!(l>=0&&l<=1))DUNE_THROW(Dune::InvalidStateException,"SalinityBuoyancyScale must lie in [0,1]");
   return l;
  }();
  return v;
 }
};
// Reference liquid mole fractions (water, air, NaCl) for rho_ref; set once by
// the problem before any volume variables are evaluated.
struct BuoyancyReference {
 static std::array<double,3>& moleFractions(){static std::array<double,3> x{{-1,-1,-1}};return x;}
 static bool& registered(){static bool r=false;return r;}
 static void set(const std::array<double,3>& x){moleFractions()=x;registered()=true;}
};
}
#endif
