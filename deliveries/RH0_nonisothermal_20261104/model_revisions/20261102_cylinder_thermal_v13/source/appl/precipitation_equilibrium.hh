#ifndef CYLINDER_PRECIPITATION_EQUILIBRIUM_HH
#define CYLINDER_PRECIPITATION_EQUILIBRIUM_HH
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace HeterogeneityRevision {
inline double saturationMolality(double saltMassFraction,double saltMolarMass){
 if(!(saltMassFraction>0&&saltMassFraction<1&&saltMolarMass>0))throw std::runtime_error("Invalid solubility definition");
 return saltMassFraction/(saltMolarMass*(1-saltMassFraction));
}
// n_s >= 0, capacity gap >= 0 and n_s*gap=0. Both inputs are mol/m3 bulk.
inline double precipitationComplementarity(double solidMoles,double capacityGap){
 if(!std::isfinite(solidMoles)||!std::isfinite(capacityGap))throw std::runtime_error("Nonfinite mineral state");
 return std::min(solidMoles,capacityGap);
}
}
#endif
