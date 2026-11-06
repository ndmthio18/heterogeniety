# Baseline provenance

The authoritative baseline is Git commit
`469b6a95edd685a990dc7fea1780221be571d3a9` on
`research/greal-experimental-bottom-hpcc`.

| Item | Verified identity |
|---|---|
| Baseline source Git tree | `beaad6ef174678ac5fde43fb940db4f80ab5e7e5` |
| `inputs/Greal-81.input` Git blob | `e4aee07ed8018c2da6d4e51b345bac5070db415a` |
| `inputs/Greal-81.input` SHA256 | `77af509ab2ac95e2597ff6d975c90953a0371ac32dd667c86083e14e527b5d81` |
| Original deployed HPCC solver SHA256 | `563e805f191faf31e44faf35e1f90ea92e05f019e1719cac8bdd9f473a55bd23` |
| Integrated portable r03 solver SHA256 | `daacab36ed1e16057e4db325aebf39aab22737e74232ac45ea8826059e07156c` |

The accepted Greal-81 run reached 174 h evaporation after 2 h
pre-equilibration. Its 1--174 h reservoir-solution loss was 52.4057 g versus
51.52 g observed (+1.719%). That prior agreement is not a new validation of
the causal switches and is not used to recalibrate any case in this campaign.

The causal implementation was traced to commit
`bcef89527e0935fde9e9ec6ee176a70499695840`; its source tree is
`f4e7ed42b99924ae7630f1250e34fc7a73f9228c`. The port is an explicit source
integration, not a binary substitution.
