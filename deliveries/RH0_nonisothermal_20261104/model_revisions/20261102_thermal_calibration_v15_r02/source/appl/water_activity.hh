#ifndef HETEROGENEITY_WATER_ACTIVITY_HH
#define HETEROGENEITY_WATER_ACTIVITY_HH
#include <cmath>
#include <stdexcept>
#include <vector>
namespace HeterogeneityRevision {
// Pure NaCl Pitzer osmotic coefficient: Rose et al. (2008), Appendix A,
// Eqs. A15-A16 and Table A5 (Pitzer and Mayorga 1973 parameters, 298.15 K).
// Use at 293.15 K is a stated near-room-temperature approximation, not a fit.
// v09: retain the formula; extend evaluation to m=8 for Newton trial states.
// Accepted equilibrium states are checked against the inherited w_sat=0.26
// (m_sat=6.011884), only 0.2% beyond the previous diagnostic limit of 6.
// This is not validation of supersaturated states or a nucleation model.
// m is mol NaCl / kg water, NOT the solution molarity used for output plots.
inline double naclWaterActivity(double m, double waterMolarMass)
{
 if(!std::isfinite(m)||m<0||m>8||!std::isfinite(waterMolarMass)||waterMolarMass<=0)
  throw std::runtime_error("NaCl water activity requires trial molality must stay in [0,8]; accepted mineral equilibrium checked separately");
 const auto r=std::sqrt(m);
 const auto phi=1-.3915*r/(1+1.2*r)+m*(.0765+.2664*std::exp(-2*r))+m*m*.00127;
 return std::exp(-2*m*waterMolarMass*phi);
}
// Positive driving is required; do not silently replace condensation by zero.
inline std::vector<double> normalizedEvaporationWeights(const std::vector<double>& aw,
 const std::vector<double>& area, double relativeVaporPressure)
{
 if(aw.empty()||aw.size()!=area.size()||!std::isfinite(relativeVaporPressure)
    ||relativeVaporPressure<0||relativeVaporPressure>=1)
  throw std::runtime_error("Invalid local evaporation weighting inputs");
 double sum=0,total=0;std::vector<double> weights(aw.size());
 for(std::size_t i=0;i<aw.size();++i){
  if(!std::isfinite(aw[i])||aw[i]>1||!(aw[i]>relativeVaporPressure)
     ||!std::isfinite(area[i])||area[i]<=0)
   throw std::runtime_error("Water activity weighting requires positive evaporation driving and area");
  weights[i]=aw[i]-relativeVaporPressure;sum+=area[i]*weights[i];total+=area[i];
 }
 for(auto& w:weights)w*=total/sum;
 return weights;
}
}
#endif
