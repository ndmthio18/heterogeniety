#!/bin/bash
# Navigate to the build directory
cd /home/zhixin/Documents/Cooperation_Ali/dumux/DUMUX/kiemle2025a/build-cmake/appl/ || exit 1

# Compile the executable
make test_stability_2pncmin_BC_analysis_tpfa || exit 1

# ======================================================================
# Test sand F36 
# ======================================================================
# Run base case 
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_F36 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 6.94e-8 -FreeFlow.BoundaryLayerThickness 0.012642 -SpatialParams.referencePorosity 0.39 -SpatialParams.referencePermeability 7.64e-12 -SpatialParams.Snr 0 -SpatialParams.Swr 0.05 -SpatialParams.BrooksCoreyPcEntry 0.469e4 -SpatialParams.BrooksCoreyLambda 5.04

# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_F36_E_input -FreeFlow.EvaporationType InputFile -FreeFlow.EvaporationRateDataFile ../../../appl/2pncmin_BC/datafiles/evaporationrate_F36.txt -FreeFlow.BoundaryLayerThickness 0.012642 -SpatialParams.referencePorosity 0.39 -SpatialParams.referencePermeability 7.64e-12 -SpatialParams.Snr 0 -SpatialParams.Swr 0.05 -SpatialParams.BrooksCoreyPcEntry 0.469e4 -SpatialParams.BrooksCoreyLambda 5.04

# ======================================================================
# Test sand W3
# ======================================================================
# Run base case
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_W3 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 5.21e-8 -FreeFlow.BoundaryLayerThickness 0.003019 -SpatialParams.referencePorosity 0.39 -SpatialParams.referencePermeability 3.13e-14 -SpatialParams.Snr 0 -SpatialParams.Swr 0.205 -SpatialParams.BrooksCoreyPcEntry 1.12e4 -SpatialParams.BrooksCoreyLambda 0.384

# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_W3_E_input -FreeFlow.EvaporationType InputFile -FreeFlow.EvaporationRateDataFile ../../../appl/2pncmin_BC/datafiles/evaporationrate_W3.txt -FreeFlow.BoundaryLayerThickness 0.003019 -SpatialParams.referencePorosity 0.39 -SpatialParams.referencePermeability 3.13e-14 -SpatialParams.Snr 0 -SpatialParams.Swr 0.205 -SpatialParams.BrooksCoreyPcEntry 1.12e4 -SpatialParams.BrooksCoreyLambda 0.384

# ======================================================================
# Test sand W3 - Porosity variation
# ======================================================================
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_W3_P031 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 5.21e-8 -FreeFlow.BoundaryLayerThickness 0.003019 -SpatialParams.referencePorosity 0.31 -SpatialParams.referencePermeability 3.13e-14 -SpatialParams.Snr 0 -SpatialParams.Swr 0.25 -SpatialParams.BrooksCoreyPcEntry 1.12e4 -SpatialParams.BrooksCoreyLambda 0.384

# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_W3_P036 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 5.21e-8 -FreeFlow.BoundaryLayerThickness 0.003019 -SpatialParams.referencePorosity 0.36 -SpatialParams.referencePermeability 3.13e-14 -SpatialParams.Snr 0 -SpatialParams.Swr 0.22 -SpatialParams.BrooksCoreyPcEntry 1.12e4 -SpatialParams.BrooksCoreyLambda 0.384

# ======================================================================
# Run base cases (ACTIVE)
# ======================================================================

./test_stability_2pncmin_BC_analysis_tpfa \
  -Problem.Name test_W3_2 \
  -FreeFlow.EvaporationType Constant \
  -FreeFlow.EvaporationRate 5.79e-8 \
  -FreeFlow.BoundaryLayerThickness 0.003019 \
  -SpatialParams.referencePorosity 0.36 \
  -SpatialParams.referencePermeability 3.13e-14 \
  -SpatialParams.Snr 0 \
  -SpatialParams.Swr 0.22 \
  -SpatialParams.BrooksCoreyPcEntry 1.12e4 \
  -SpatialParams.BrooksCoreyLambda 0.384

./test_stability_2pncmin_BC_analysis_tpfa \
  -Problem.Name test_F36_2 \
  -FreeFlow.EvaporationType Constant \
  -FreeFlow.EvaporationRate 6.94e-8 \
  -FreeFlow.BoundaryLayerThickness 0.012642 \
  -SpatialParams.referencePorosity 0.4 \
  -SpatialParams.referencePermeability 7.64e-12 \
  -SpatialParams.Snr 0 \
  -SpatialParams.Swr 0.05 \
  -SpatialParams.BrooksCoreyPcEntry 0.469e4 \
  -SpatialParams.BrooksCoreyLambda 5.04

# ======================================================================
# Analyse temperature (commented)
# ======================================================================
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_F36_T1 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 6.94e-8 -FreeFlow.BoundaryLayerThickness 0.012642 -SpatialParams.referencePorosity 0.4 -SpatialParams.referencePermeability 7.64e-12 -SpatialParams.Snr 0 -SpatialParams.Swr 0.05 -SpatialParams.BrooksCoreyPcEntry 0.469e4 -SpatialParams.BrooksCoreyLambda 5.04 -SpatialParams.Temperature 288.15 -FreeFlow.AirTemperature 288.15
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_F36_T2 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 6.94e-8 -FreeFlow.BoundaryLayerThickness 0.012642 -SpatialParams.referencePorosity 0.4 -SpatialParams.referencePermeability 7.64e-12 -SpatialParams.Snr 0 -SpatialParams.Swr 0.05 -SpatialParams.BrooksCoreyPcEntry 0.469e4 -SpatialParams.BrooksCoreyLambda 5.04 -SpatialParams.Temperature 298.15 -FreeFlow.AirTemperature 298.15
# ./test_stability_2pncmin_BC_analysis_tpfa -Problem.Name test_F36_T3 -FreeFlow.EvaporationType Constant -FreeFlow.EvaporationRate 6.94e-8 -FreeFlow.BoundaryLayerThickness 0.012642 -SpatialParams.referencePorosity 0.4 -SpatialParams.referencePermeability 7.64e-12 -SpatialParams.Snr 0 -SpatialParams.Swr 0.05 -SpatialParams.BrooksCoreyPcEntry 0.469e4 -SpatialParams.BrooksCoreyLambda 5.04 -SpatialParams.Temperature 303.15 -FreeFlow.AirTemperature 303.15
