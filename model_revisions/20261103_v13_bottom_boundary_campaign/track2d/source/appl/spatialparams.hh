// -*- mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
// vi: set et ts=4 sw=4 sts=4:
/*****************************************************************************
 *   See the file COPYING for full copying permissions.                      *
 *                                                                           *
 *   This program is free software: you can redistribute it and/or modify    *
 *   it under the terms of the GNU General Public License as published by    *
 *   the Free Software Foundation, either version 3 of the License, or       *
 *   (at your option) any later version.                                     *
 *                                                                           *
 *   This program is distributed in the hope that it will be useful,         *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the            *
 *   GNU General Public License for more details.                            *
 *                                                                           *
 *   You should have received a copy of the GNU General Public License       *
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.   *
 *****************************************************************************/
/*!
 * \file
 * \ingroup TwoPNCMinTests
 * \brief Spatial parameters for the salinization problem, where evaporation
 * from a porous medium saturated wit brine and air leads to precipitation of salt.
 */

#ifndef DUMUX_SALINIZATION_SPATIAL_PARAMETERS_HH
#define DUMUX_SALINIZATION_SPATIAL_PARAMETERS_HH

#include <dumux/common/math.hh>
#include <dumux/io/gnuplotinterface.hh>
#include <dumux/io/plotpckrsw.hh>
#include <dumux/io/ploteffectivediffusivitymodel.hh>
#include <dumux/io/plotthermalconductivitymodel.hh>
#include <dumux/porousmediumflow/properties.hh>
#include <dumux/porousmediumflow/fvspatialparamsmp.hh>
#include <dumux/material/fluidmatrixinteractions/2p/brookscorey.hh>
#include <dumux/material/fluidmatrixinteractions/2p/vangenuchten.hh>
#include <dumux/material/fluidmatrixinteractions/porosityprecipitation.hh>
#include <dumux/material/fluidmatrixinteractions/permeabilitykozenycarman.hh>

namespace Dumux {

/*!
 * \ingroup TwoPNCMinTests
 * \brief Spatial parameters for the salinization problem, where evaporation
 * from a porous medium saturated wit brine and air leads to precipitation of salt.
 */
template<class GridGeometry, class Scalar>
class SalinizationSpatialParams
: public FVPorousMediumFlowSpatialParamsMP<GridGeometry, Scalar,
                         SalinizationSpatialParams<GridGeometry, Scalar>>
{
    using GridView = typename GridGeometry::GridView;
    using FVElementGeometry = typename GridGeometry::LocalView;
    using SubControlVolume = typename FVElementGeometry::SubControlVolume;
    using Element = typename GridView::template Codim<0>::Entity;

    using ParentType = FVPorousMediumFlowSpatialParamsMP<GridGeometry, Scalar,
                                       SalinizationSpatialParams<GridGeometry, Scalar>>;

    static constexpr int dimWorld = GridView::dimensionworld;

    using PcKrSwCurve = FluidMatrix::BrooksCoreyDefault<Scalar>;
    using GlobalPosition = typename SubControlVolume::GlobalPosition;

public:
    // type used for the permeability (i.e. tensor or scalar)
    using PermeabilityType = Scalar;
    //! Export the material law type used

    SalinizationSpatialParams(std::shared_ptr<const GridGeometry> gridGeometry)
    : ParentType(gridGeometry)
    , coarsePcKrSwCurve_(getParam<std::string>("SpatialParams.CoarsePcGroup", "SpatialParams"))
    , finePcKrSwCurve_(getParam<std::string>("SpatialParams.FinePcGroup", "SpatialParams"))
    , filterPcKrSwCurve_(getParam<std::string>("SpatialParams.FilterPcGroup", "SpatialParams.CoarseMaterial"))
    {
        solubilityLimit_       = getParam<Scalar>("SpatialParams.SolubilityLimit", 0.26);
        const auto basePorosity = getParam<Scalar>("SpatialParams.referencePorosity", 0.11);
        coarsePorosity_        = getParam<Scalar>("SpatialParams.CoarsePorosity", basePorosity);
        finePorosity_          = getParam<Scalar>("SpatialParams.FinePorosity", basePorosity);

        const auto basePermeability = getParam<Scalar>("SpatialParams.referencePermeability", 2.23e-14);
        coarsePermeability_    = getParam<Scalar>("SpatialParams.CoarsePermeability", basePermeability);
        finePermeability_      = getParam<Scalar>("SpatialParams.FinePermeability", basePermeability);

        splitAxis_ = getParam<int>("SpatialParams.SplitAxis", 0);

        const auto& gridGeometryRef = this->gridGeometry();
        const auto& bBoxMin = gridGeometryRef.bBoxMin();
        const auto& bBoxMax = gridGeometryRef.bBoxMax();
        const auto defaultSplit = bBoxMin[splitAxis_] + 0.5*(bBoxMax[splitAxis_] - bBoxMin[splitAxis_]);
        splitCoordinate_ = getParam<Scalar>("SpatialParams.SplitCoordinate", defaultSplit);

        temperature_  = getParam<Scalar>("SpatialParams.Temperature");
    }

    /*!
     * \brief Returns the temperature in the domain at the given position
     * \param globalPos The position in global coordinates where the temperature should be specified.
     */
    GlobalPosition gravity(const GlobalPosition&) const { GlobalPosition g(0.); g[1]=-9.81; return g; }

    Scalar temperatureAtPos(const GlobalPosition& globalPos) const
    {
        return temperature_;
    }

    /*!
     *  \brief Defines the minimum porosity \f$[-]\f$ distribution
     *
     *  \param element The finite element
     *  \param scv The sub-control volume
     */
    Scalar minimalPorosity(const Element& element, const SubControlVolume &scv) const
    { return 1e-5; }

    /*!
     *  \brief Defines the volume fraction of the inert component
     *
     *  \param globalPos The global position in the domain
     *  \param compIdx The index of the inert solid component
     */
    template<class SolidSystem>
    Scalar inertVolumeFractionAtPos(const GlobalPosition& globalPos, int compIdx) const
    { return 1.0-referencePorosityAtPos_(globalPos); }

    /*!
     *  \brief Defines the reference porosity \f$[-]\f$ distribution.
     *
     *  This is the porosity of the porous medium without any of the
     *  considered solid phases.
     *
     *  \param element The finite element
     *  \param scv The sub-control volume
     */
    Scalar referencePorosity(const Element& element, const SubControlVolume &scv) const
    { return referencePorosityAtPos_(scv.center()); }

    /*! Intrinsic permeability tensor K \f$[m^2]\f$ depending
     *  on the position in the domain
     *
     *  \param element The finite volume element
     *  \param scv The sub-control volume
     *  \param elemSol The element solution
     *
     *  Solution dependent permeability function
     */
    template<class ElementSolution>
    PermeabilityType permeability(const Element& element,
                                  const SubControlVolume& scv,
                                  const ElementSolution& elemSol) const
    {
        if (fixedHydraulics_)
            return referencePermeabilityAtPos_(scv.center());
        auto priVars = evalSolution(element, element.geometry(), elemSol, scv.center(), /*ignoreState=*/true);

        Scalar sumPrecipitates = priVars[/*numComp*/3];

        using std::max;
        const auto referencePorosity = referencePorosityAtPos_(scv.center());
        const auto referencePermeability = referencePermeabilityAtPos_(scv.center());
        const auto poro = max(/*minPoro*/1e-5, referencePorosity - sumPrecipitates);
        return permLaw_.evaluatePermeability(referencePermeability, referencePorosity, poro);
    }

    // the solubility limit of NaCl
    Scalar solubilityLimit() const
    { return solubilityLimit_; }

    Scalar theta(const SubControlVolume &scv) const
    { return 10.0; }

    /*!
     * \brief Returns the fluid-matrix interaction law at a given location
     * \param globalPos A global coordinate vector
     */
    auto fluidMatrixInteractionAtPos(const GlobalPosition &globalPos) const
    {
        return isFilter(globalPos) ? makeFluidMatrixInteraction(filterPcKrSwCurve_) : isCoarse_(globalPos)
            ? makeFluidMatrixInteraction(coarsePcKrSwCurve_)
            : makeFluidMatrixInteraction(finePcKrSwCurve_);
    }

    // define which phase is to be considered as the wetting phase
    template<class FluidSystem>
    int wettingPhaseAtPos(const GlobalPosition& globalPos) const
    { return FluidSystem::H2OIdx; }

    Scalar extrusionFactorAtPos(const GlobalPosition& globalPos) const
    {
        return getParam<Scalar>("Geometry.ExtrusionWidth", .039269908169872414);
    }



    bool fixedHydraulics() const { return fixedHydraulics_; }
    bool isFilter(const GlobalPosition& p) const {return explicitFilter_ && p[1]<-1e-10;}
    Scalar registeredPermeability(const GlobalPosition& p)const{return referencePermeabilityAtPos_(p);}

private:
    const bool fixedHydraulics_ = getParam<bool>("Revision.FixedHydraulics", false);

    bool isCoarse_(const GlobalPosition& globalPos) const
    { return globalPos[splitAxis_] <= splitCoordinate_; }

    Scalar referencePorosityAtPos_(const GlobalPosition& globalPos) const
    { return isFilter(globalPos) ? filterPorosity_ : (isCoarse_(globalPos) ? coarsePorosity_ : finePorosity_); }

    PermeabilityType referencePermeabilityAtPos_(const GlobalPosition& globalPos) const
    { return isFilter(globalPos) ? filterPermeability_ : (isCoarse_(globalPos) ? coarsePermeability_ : finePermeability_); }

    PermeabilityKozenyCarman<PermeabilityType> permLaw_;

    Scalar solubilityLimit_;
    Scalar coarsePorosity_;
    Scalar finePorosity_;
    PermeabilityType coarsePermeability_ = 0.0;
    PermeabilityType finePermeability_ = 0.0;
    Scalar splitCoordinate_ = 0.0;
    int splitAxis_ = 0;
    const PcKrSwCurve coarsePcKrSwCurve_;
    const PcKrSwCurve finePcKrSwCurve_;
    const PcKrSwCurve filterPcKrSwCurve_;
    const bool explicitFilter_=getParam<bool>("Revision.ExplicitFilter",false);
    const Scalar filterPorosity_=getParam<Scalar>("SpatialParams.FilterPorosity",.35);
    const Scalar filterPermeability_=getParam<Scalar>("SpatialParams.FilterPermeability",1e-11);
    Scalar temperature_;
};

} // end namespace Dumux

#endif
