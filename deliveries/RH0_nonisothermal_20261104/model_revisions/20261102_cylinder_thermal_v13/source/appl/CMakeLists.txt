dune_symlink_to_source_files(FILES params.input)

dumux_add_test(NAME test_stability_2pncmin_BC_analysis_tpfa
              SOURCES main.cc
              COMPILE_DEFINITIONS TYPETAG=SaltExperimentsCCTpfa NONISOTHERMAL=1 REDUCEDOUTPUT=1
)

