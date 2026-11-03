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
 * \brief The properties of the problem where brine is evaporating at the top boundary. The system is closed at the remaining boundaries.
 */
#ifndef DUMUX_SALT_EXPERIMENTS_PROPERTIES_HH
#define DUMUX_SALT_EXPERIMENTS_PROPERTIES_HH


#include <dune/grid/uggrid.hh>
#include <random>

#include <dumux/discretization/elementsolution.hh>
#include <dumux/discretization/method.hh>
#include <dumux/discretization/cctpfa.hh>
#include "cylinder_geometry.hh"
// Load the local composition overlay before the upstream model header's
// relative include can claim its identical include guard.
#include <dumux/porousmediumflow/2pnc/volumevariables.hh>
#include <dumux/porousmediumflow/2pncmin/model.hh>
#ifndef CYLINDER_UNIFIED_VOLUME_VARIABLES_ACTIVE
#error "Cylinder unified phase-composition overlay was not selected"
#endif

#include <dumux/porousmediumflow/problem.hh>
#include <dumux/material/fluidsystems/brineair.hh>
#include "transport_fluidsystem.hh"

#include <dumux/material/components/nacl.hh>
#include <dumux/material/components/granite.hh>
#include <dumux/material/solidsystems/compositionalsolidphase.hh>

#include "spatialparams.hh"
#include "problem.hh"
#include "equilibrium_localresidual.hh"

//
namespace Dumux::Properties {

// Create new type tags
namespace TTag {
#if NONISOTHERMAL
    struct SaltExperiments { using InheritsFrom = std::tuple<TwoPNCMinNI>;};
#else
    struct SaltExperiments { using InheritsFrom = std::tuple<TwoPNCMin>; };
#endif
struct SaltExperimentsCCTpfa { using InheritsFrom = std::tuple<SaltExperiments,CCTpfaModel>; };
} // end namespace TTag


// Set the grid type
template<class TypeTag>
struct Grid<TypeTag, TTag::SaltExperiments>
{
    using Scalar = GetPropType<TypeTag, Properties::Scalar>;
    using type = Dune::UGGrid<2>;
};


// Set the problem property
template<class TypeTag>struct EnableGridGeometryCache<TypeTag,TTag::SaltExperiments>{static constexpr bool value=true;};
template<class TypeTag>struct EnableGridVolumeVariablesCache<TypeTag,TTag::SaltExperiments>{static constexpr bool value=true;};
template<class TypeTag>struct EnableGridFluxVariablesCache<TypeTag,TTag::SaltExperiments>{static constexpr bool value=true;};
template<class TypeTag>
struct Problem<TypeTag, TTag::SaltExperiments> { using type = SaltExperimentsProblem<TypeTag>; };


template<class TypeTag>
struct LocalResidual<TypeTag,TTag::SaltExperiments> { using type=EquilibriumMineralizationLocalResidual<TypeTag>; };

template<class TypeTag>
struct FluidSystem<TypeTag, TTag::SaltExperiments>
{
    using Scalar = GetPropType<TypeTag, Properties::Scalar>;
    using type = HeterogeneityTransportFluidSystem<Scalar>;
};


template<class TypeTag>
struct SolidSystem<TypeTag, TTag::SaltExperiments>
{
    using Scalar = GetPropType<TypeTag, Properties::Scalar>;
    using ComponentOne = Components::NaCl<Scalar>;
    using ComponentTwo = Components::Granite<Scalar>;
    static constexpr int numInertComponents = 1;
    using type = SolidSystems::CompositionalSolidPhase<Scalar, ComponentOne, ComponentTwo, numInertComponents>;
};

// Set the spatial parameters
template<class TypeTag>
struct SpatialParams<TypeTag, TTag::SaltExperiments>
{
    using GridGeometry = GetPropType<TypeTag, Properties::GridGeometry>;
    using Scalar = GetPropType<TypeTag, Properties::Scalar>;
    using type = SalinizationSpatialParams<GridGeometry, Scalar>;
};



//template<class TypeTag>
//struct ReplaceCompEqIdx<TypeTag, TTag::SaltExperiments> { static constexpr int value = 1; }; //!< Replace gas balance by total mass balance

template<class TypeTag>
struct Formulation<TypeTag, TTag::SaltExperiments>
{ static constexpr auto value = TwoPFormulation::p0s1; };

} // end namespace Dumux::Properties

#endif
