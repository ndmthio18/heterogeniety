# Bottom and interface comparison — new results pending

Use native FV face fluxes. Gross inflow/outflow must be split per face, then integrated over accepted steps. In2D all areas and volumes include the same extrusion factor. The native record distinguishes external reservoir faces(kind0), sand interface(kind1), sand/filter exchange(kind3), midfilter vertical(kind4) and horizontal filter transport(kind5). For G, external bottom supply is not directly F36 sand supply: report kind3 and filter storage separately.

Evaluate outgoing liquid concentration, gross salt loss, net bottom supply, F36→W3 advective and reverse diffusive exchange, and net lateral export without imposing their signs. Use actual signs, not mechanism labels as assumptions. Explain F36 retention using the full signed balance and seed impulses, not net supply alone.

The earlier6.889/5.317g gross inflow/outflow and1.573/1.342g net bottom/interface figures belong to the v12 native replay audit. They must not be relabelled as v13 fluxes. New accepted accelerated v13 B0 and modified-case ledgers will provide matched nonisothermal comparisons. No new mechanism result exists at submission.
