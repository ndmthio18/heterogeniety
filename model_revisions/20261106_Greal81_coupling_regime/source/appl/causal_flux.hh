#ifndef HETEROGENEITY_CAUSAL_FLUX_HH
#define HETEROGENEITY_CAUSAL_FLUX_HH
// v10 causal switches. Both act inside the flux laws used by the assembled
// residual (and hence the numeric Jacobian, the accepted-step audit and the
// velocity diagnostics); no diagnostic is zeroed separately.
//
// Revision.InterfaceExchangeEnabled (default true): false makes every interior
// face whose two cells lie in different materials a zero-thickness impermeable
// partition. Darcy fluxes of both phases (hence advection of all components)
// and Fickian fluxes of all components in both phases are exactly zero there.
// Cells, volumes, top area and bottom/reservoir boundary are unchanged.
//
// Revision.SalinityBuoyancyScale lambda (default 1): the liquid density in the
// Darcy gravity term is rho_g=rho_ref(p,T,x_ref)+lambda*(rho-rho_ref), where
// x_ref is the 1 M reservoir liquid composition (registered by the problem)
// evaluated at the local liquid pressure and temperature. lambda=1 calls the
// unmodified upstream law. Gas-phase gravity, storage densities, viscosity,
// diffusion and water activity keep the actual composition.
#include <array>
#include <cmath>
#include <dune/common/exceptions.hh>
#include <dumux/common/math.hh>
#include <dumux/common/parameters.hh>
#include <dumux/common/properties.hh>
#include <dumux/discretization/extrusion.hh>
#include <dumux/discretization/cellcentered/tpfa/computetransmissibility.hh>
#include <dumux/flux/darcyslaw.hh>
#include <dumux/flux/fickslaw.hh>
#include "causal_switches.hh"
namespace HeterogeneityCausal {
template<class TypeTag>
class CausalDarcysLaw:public Dumux::DarcysLaw<TypeTag> {
 using Base=Dumux::DarcysLaw<TypeTag>;
 using GG=Dumux::GetPropType<TypeTag,Dumux::Properties::GridGeometry>;
 using Extrusion=Dumux::Extrusion_t<GG>;
 using FS=Dumux::GetPropType<TypeTag,Dumux::Properties::FluidSystem>;
public:
 using Scalar=Dumux::GetPropType<TypeTag,Dumux::Properties::Scalar>;
 template<class Problem,class Element,class FVG,class EVV,class SCVF,class EFC>
 static Scalar flux(const Problem& problem,const Element& element,const FVG& fvGeometry,const EVV& elemVolVars,const SCVF& scvf,int phaseIdx,const EFC& elemFluxVarsCache){
  if(problem.interfaceExchangeBlocked(fvGeometry,scvf))return 0.0;
  const double lambda=Switches::buoyancyScale();
  if(lambda==1.0||phaseIdx!=FS::liquidPhaseIdx)return Base::flux(problem,element,fvGeometry,elemVolVars,scvf,phaseIdx,elemFluxVarsCache);
  return scaledFlux(problem,element,fvGeometry,elemVolVars,scvf,phaseIdx,elemFluxVarsCache,lambda);
 }
 // Line-by-line copy of the upstream dumux-3.7 CCTpfaDarcysLaw (non-network)
 // gravity branch, with density(phase) replaced by the scaled buoyancy density.
 // Exposed for the self-test, which checks lambda=1 against the upstream law.
 template<class Problem,class Element,class FVG,class EVV,class SCVF,class EFC>
 static Scalar scaledFlux(const Problem& problem,const Element&,const FVG& fvGeometry,const EVV& elemVolVars,const SCVF& scvf,int phaseIdx,const EFC& elemFluxVarsCache,Scalar lambda){
  static const bool enableGravity=Dumux::getParamFromGroup<bool>(problem.paramGroup(),"Problem.EnableGravity");
  const auto& fluxVarsCache=elemFluxVarsCache[scvf];
  const auto& insideScv=fvGeometry.scv(scvf.insideScvIdx());
  const auto& insideVolVars=elemVolVars[insideScv];
  const auto& outsideVolVars=elemVolVars[scvf.outsideScvIdx()];
  const auto pInside=insideVolVars.pressure(phaseIdx);
  const auto pOutside=outsideVolVars.pressure(phaseIdx);
  if(!enableGravity)return fluxVarsCache.advectionTij()*(pInside-pOutside);
  const auto rho=scvf.boundary()?outsideVolVars.scaledBuoyancyDensity(phaseIdx,lambda)
   :(insideVolVars.scaledBuoyancyDensity(phaseIdx,lambda)+outsideVolVars.scaledBuoyancyDensity(phaseIdx,lambda))*0.5;
  const auto& tij=fluxVarsCache.advectionTij();
  const auto& g=problem.spatialParams().gravity(scvf.ipGlobal());
  const auto alpha_inside=Dumux::vtmv(scvf.unitOuterNormal(),insideVolVars.permeability(),g)*insideVolVars.extrusionFactor();
  Scalar flux=tij*(pInside-pOutside)+rho*Extrusion::area(fvGeometry,scvf)*alpha_inside;
  if(!scvf.boundary()){
   const auto& outsideScv=fvGeometry.scv(scvf.outsideScvIdx());
   const auto outsideK=outsideVolVars.permeability();
   const auto outsideTi=fvGeometry.gridGeometry().isPeriodic()
    ?Dumux::computeTpfaTransmissibility(fvGeometry,fvGeometry.flipScvf(scvf.index()),outsideScv,outsideK,outsideVolVars.extrusionFactor())
    :-1.0*Dumux::computeTpfaTransmissibility(fvGeometry,scvf,outsideScv,outsideK,outsideVolVars.extrusionFactor());
   const auto alpha_outside=Dumux::vtmv(scvf.unitOuterNormal(),outsideK,g)*outsideVolVars.extrusionFactor();
   flux-=rho*tij/outsideTi*(alpha_inside-alpha_outside);
  }
  return flux;
 }
 // Upstream law, for the self-test only.
 template<class Problem,class Element,class FVG,class EVV,class SCVF,class EFC>
 static Scalar upstreamFlux(const Problem& problem,const Element& element,const FVG& fvGeometry,const EVV& elemVolVars,const SCVF& scvf,int phaseIdx,const EFC& elemFluxVarsCache)
 {return Base::flux(problem,element,fvGeometry,elemVolVars,scvf,phaseIdx,elemFluxVarsCache);}
};
template<class TypeTag>
class CausalFicksLaw:public Dumux::FicksLaw<TypeTag> {
 using Base=Dumux::FicksLaw<TypeTag>;
 using Scalar=Dumux::GetPropType<TypeTag,Dumux::Properties::Scalar>;
 static constexpr int numComponents=Dumux::GetPropType<TypeTag,Dumux::Properties::ModelTraits>::numFluidComponents();
 using ComponentFluxVector=Dune::FieldVector<Scalar,numComponents>;
public:
 template<class Problem,class Element,class FVG,class EVV,class SCVF,class EFC>
 static ComponentFluxVector flux(const Problem& problem,const Element& element,const FVG& fvGeometry,const EVV& elemVolVars,const SCVF& scvf,int phaseIdx,const EFC& elemFluxVarsCache){
  if(problem.interfaceExchangeBlocked(fvGeometry,scvf))return ComponentFluxVector(0.0);
  return Base::flux(problem,element,fvGeometry,elemVolVars,scvf,phaseIdx,elemFluxVarsCache);
 }
 template<class Problem,class Element,class FVG,class VV,class SCVF,class EFC>
 static ComponentFluxVector flux(const Problem& problem,const Element& element,const FVG& fvGeometry,const VV& insideVolVars,const VV& outsideVolVars,const SCVF& scvf,int phaseIdx,const EFC& elemFluxVarsCache){
  if(problem.interfaceExchangeBlocked(fvGeometry,scvf))return ComponentFluxVector(0.0);
  return Base::flux(problem,element,fvGeometry,insideVolVars,outsideVolVars,scvf,phaseIdx,elemFluxVarsCache);
 }
};
}
#endif
