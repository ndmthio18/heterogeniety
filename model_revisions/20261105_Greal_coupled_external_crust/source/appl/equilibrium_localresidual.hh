#ifndef CYLINDER_EQUILIBRIUM_LOCALRESIDUAL_HH
#define CYLINDER_EQUILIBRIUM_LOCALRESIDUAL_HH
#include <dumux/porousmediumflow/mineralization/localresidual.hh>
namespace Dumux {
template<class TypeTag>
class EquilibriumMineralizationLocalResidual : public MineralizationLocalResidual<TypeTag> {
 using Parent=MineralizationLocalResidual<TypeTag>;
 using Problem=GetPropType<TypeTag,Properties::Problem>;
 using FS=GetPropType<TypeTag,Properties::FluidSystem>;
 using VV=GetPropType<TypeTag,Properties::VolumeVariables>;
 using SCV=typename GetPropType<TypeTag,Properties::GridGeometry>::LocalView::SubControlVolume;
public:
 using Parent::Parent;
 auto computeStorage(const Problem& problem,const SCV& scv,const VV& v)const {
  auto n=Parent::computeStorage(problem,scv,v);
#if NONISOTHERMAL
  n[GetPropType<TypeTag,Properties::ModelTraits>::Indices::energyEqIdx]
      += problem.externalSaltEnergyDensity(scv,v);
#endif
  if(problem.equilibriumPrecipitation()){
   static_assert(getPropValue<TypeTag,Properties::UseMoles>(),"Equilibrium mineral row uses molar storage");
   n[FS::NaClIdx]+=n[FS::numComponents];
   n[FS::numComponents]=0;
  }
  return n;
 }
};
}
#endif
