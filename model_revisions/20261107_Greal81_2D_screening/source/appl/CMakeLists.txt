dune_symlink_to_source_files(FILES params.input)

dumux_add_test(NAME test_stability_2pncmin_BC_analysis_tpfa
              SOURCES main.cc
              COMPILE_DEFINITIONS TYPETAG=SaltExperimentsCCTpfa NONISOTHERMAL=1 REDUCEDOUTPUT=1
)

# The locally overlaid DuMuX volume variables deliberately reuse the exact
# phase-equilibrium and causal-switch headers from this application directory.
target_include_directories(test_stability_2pncmin_BC_analysis_tpfa
                           PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

