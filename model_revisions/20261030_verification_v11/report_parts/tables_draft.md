| case | E_W3 0–3 mm 2 h | E_W3 0–3 mm 4 h | E_W3 0–3 mm 8 h | E_W3 0–3 mm 12 h | E_W3 0–3 mm 24 h | E_W3 0–2 mm 24 h | E_F36 0–3 mm 24 h | E_W3 3–10 mm 24 h | E_total 24 h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| medium dt300 s1 1e-5 (A C1B1/C0B1) | +0.00031 | +0.00083 | +0.00229 | +0.00422 | +0.00431 | +0.00261 | -0.00732 | +0.01764 | -0.00229 |
| coarse | +0.00032 | +0.00085 | +0.00232 | +0.00424 | +0.00443 | +0.00270 | -0.00733 | +0.01737 | -0.00159 |
| medium dt150 | +0.00031 | +0.00083 | +0.00229 | +0.00422 | +0.00432 | +0.00261 | -0.00726 | +0.01763 | -0.00217 |

| metric (24 h, g) | min over cases | max over cases | n | sign change |
|---|---:|---:|---:|---|
| W3_inv_0_3mm@24 | +0.00431 | +0.00443 | 3 | no |
| W3_inv_0_2mm@24 | +0.00261 | +0.00270 | 3 | no |
| W3_inv_0_3mm@12 | +0.00422 | +0.00424 | 3 | no |
| F36_inv_0_3mm@24 | -0.00733 | -0.00726 | 3 | no |
| W3_inv_3_10mm@24 | +0.01737 | +0.01764 | 3 | no |
| W3_ddeep_10_40mm@24 | +0.01973 | +0.02004 | 3 | no |
| F36_ddeep_10_40mm@24 | -0.02164 | -0.02006 | 3 | no |
| W3_bottom_salt_in_g@24 | -0.21526 | -0.21509 | 3 | no |
| F36_bottom_salt_in_g@24 | +0.21280 | +0.21367 | 3 | no |
| iface_salt_net_g@24 | +0.25679 | +0.25708 | 3 | no |
| total_salt_g@24 | -0.00229 | -0.00159 | 3 | no |

| check | kind | arm | metric | t (h) | test | reference | abs diff | rel diff | tol | pass |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| dt300->150 | surface_change | C1 | F36_dinv_0_3mm | 24 | +0.04191 | +0.04197 | -0.000057 | 0.14 % | 0.02 | True |
| dt300->150 | surface_inventory | C1 | F36_inv_0_3mm | 24 | +0.11065 | +0.11071 | -0.000057 | 0.05 % | 0.02 | True |
| dt300->150 | deep_change | C1 | F36_ddeep_10_40mm | 24 | +0.09628 | +0.09624 | +0.000042 | 0.04 % | 0.05 | True |
| dt300->150 | bottom_salt | C1 | F36_bottom_salt_in_g | 24 | +0.45304 | +0.45314 | -0.000106 | 0.02 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | F36_down_salt_net_3mm_g | 24 | -0.13989 | -0.13996 | +0.000069 | 0.05 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | F36_down_salt_net_10mm_g | 24 | -0.28782 | -0.28798 | +0.000161 | 0.06 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | F36_down_salt_net_20mm_g | 24 | -0.38099 | -0.38124 | +0.000255 | 0.07 % | 0.05 | True |
| dt300->150 | core_descending_vf | C1 | F36_core_desc_vf_1e-8 | 24 | +0.16859 | +0.16908 | -0.000491 | 0.29 % | 0.05 | True |
| dt300->150 | surface_change | C1 | W3_dinv_0_3mm | 24 | +0.10522 | +0.10524 | -0.000020 | 0.02 % | 0.02 | True |
| dt300->150 | surface_inventory | C1 | W3_inv_0_3mm | 24 | +0.16709 | +0.16711 | -0.000020 | 0.01 % | 0.02 | True |
| dt300->150 | deep_change | C1 | W3_ddeep_10_40mm | 24 | +0.05465 | +0.05457 | +0.000080 | 0.15 % | 0.05 | True |
| dt300->150 | bottom_salt | C1 | W3_bottom_salt_in_g | 24 | +0.02155 | +0.02154 | +0.000008 | 0.04 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | W3_down_salt_net_3mm_g | 24 | -0.00724 | -0.00724 | +0.000009 | 0.12 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | W3_down_salt_net_10mm_g | 24 | -0.03584 | -0.03590 | +0.000058 | 0.16 % | 0.05 | True |
| dt300->150 | vertical_transport | C1 | W3_down_salt_net_20mm_g | 24 | -0.03747 | -0.03751 | +0.000036 | 0.09 % | 0.05 | True |
| dt300->150 | core_descending_vf | C1 | W3_core_desc_vf_1e-8 | 24 | +0.00000 | +0.00000 | +0.000000 | – | – |  |
| dt300->150 | interface_net | C1 | iface_salt_net_g | 24 | +0.25708 | +0.25703 | +0.000050 | 0.02 % | 0.05 | True |
| dt300->150 | interface_pos | C1 | iface_salt_pos_g | 24 | +0.29275 | +0.29268 | +0.000070 | 0.02 % | 0.05 | True |
| dt300->150 | interface_liquid_net | C1 | iface_liquid_net_mL | 24 | +3.64681 | +3.64718 | -0.000375 | 0.01 % | 0.05 | True |
| dt300->150 | surface_change | C0 | F36_dinv_0_3mm | 24 | +0.04923 | +0.04923 | -0.000002 | 0.01 % | 0.02 | True |
| dt300->150 | surface_inventory | C0 | F36_inv_0_3mm | 24 | +0.11797 | +0.11797 | -0.000002 | 0.00 % | 0.02 | True |
| dt300->150 | deep_change | C0 | F36_ddeep_10_40mm | 24 | +0.11792 | +0.11788 | +0.000038 | 0.03 % | 0.05 | True |
| dt300->150 | bottom_salt | C0 | F36_bottom_salt_in_g | 24 | +0.24024 | +0.24020 | +0.000038 | 0.02 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | F36_down_salt_net_3mm_g | 24 | -0.04923 | -0.04923 | +0.000002 | 0.01 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | F36_down_salt_net_10mm_g | 24 | -0.12231 | -0.12231 | +0.000000 | 0.00 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | F36_down_salt_net_20mm_g | 24 | -0.19413 | -0.19405 | -0.000080 | 0.04 % | 0.05 | True |
| dt300->150 | core_descending_vf | C0 | F36_core_desc_vf_1e-8 | 24 | +0.22057 | +0.22390 | -0.003321 | 1.48 % | 0.05 | True |
| dt300->150 | surface_change | C0 | W3_dinv_0_3mm | 24 | +0.10091 | +0.10092 | -0.000015 | 0.02 % | 0.02 | True |
| dt300->150 | surface_inventory | C0 | W3_inv_0_3mm | 24 | +0.16277 | +0.16279 | -0.000015 | 0.01 % | 0.02 | True |
| dt300->150 | deep_change | C0 | W3_ddeep_10_40mm | 24 | +0.03461 | +0.03459 | +0.000017 | 0.05 % | 0.05 | True |
| dt300->150 | bottom_salt | C0 | W3_bottom_salt_in_g | 24 | +0.23664 | +0.23665 | -0.000013 | 0.01 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | W3_down_salt_net_3mm_g | 24 | -0.10091 | -0.10092 | +0.000015 | 0.02 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | W3_down_salt_net_10mm_g | 24 | -0.20203 | -0.20206 | +0.000030 | 0.01 % | 0.05 | True |
| dt300->150 | vertical_transport | C0 | W3_down_salt_net_20mm_g | 24 | -0.23253 | -0.23256 | +0.000024 | 0.01 % | 0.05 | True |
| dt300->150 | core_descending_vf | C0 | W3_core_desc_vf_1e-8 | 24 | +0.00000 | +0.00000 | +0.000000 | – | – |  |
| dt300->150 | effect | E=C1-C0 | F36_inv_0_3mm | 24 | -0.00732 | -0.00726 | -0.000055 | 0.75 % | 0.02 | True |
| dt300->150 | effect | E=C1-C0 | F36_inv_0_2mm | 24 | -0.00503 | -0.00500 | -0.000037 | 0.74 % | 0.02 | True |
| dt300->150 | effect | E=C1-C0 | F36_ddeep_10_40mm | 24 | -0.02164 | -0.02164 | +0.000004 | 0.02 % | 0.05 | True |
| dt300->150 | effect | E=C1-C0 | F36_bottom_salt_in_g | 24 | +0.21280 | +0.21294 | -0.000144 | 0.07 % | 0.05 | True |
| dt300->150 | effect | E=C1-C0 | W3_inv_0_3mm | 24 | +0.00431 | +0.00432 | -0.000005 | 0.11 % | 0.02 | True |
| dt300->150 | effect | E=C1-C0 | W3_inv_0_2mm | 24 | +0.00261 | +0.00261 | -0.000003 | 0.13 % | 0.02 | True |
| dt300->150 | effect | E=C1-C0 | W3_ddeep_10_40mm | 24 | +0.02004 | +0.01997 | +0.000063 | 0.32 % | 0.05 | True |
| dt300->150 | effect | E=C1-C0 | W3_bottom_salt_in_g | 24 | -0.21509 | -0.21511 | +0.000021 | 0.01 % | 0.05 | True |
| dt300->150 | onset | C1 | onset_F36_all_thr1.0e-08 | - | +6.66667 | +6.66667 | +0.000000 | – | 10 min | True |
| dt300->150 | onset | C1 | onset_F36_core_thr1.0e-08 | - | 10.2 | 10.2 | +0.000000 | – | 10 min | True |
| dt300->150 | onset | C1 | onset_W3_all_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| dt300->150 | onset | C1 | onset_W3_core_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| dt300->150 | onset | C0 | onset_F36_all_thr1.0e-08 | - | 14 | 14 | +0.000000 | – | 10 min | True |
| dt300->150 | onset | C0 | onset_F36_core_thr1.0e-08 | - | 14.2 | 14.3 | -0.166667 | – | 10 min | True |
| dt300->150 | onset | C0 | onset_W3_all_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| dt300->150 | onset | C0 | onset_W3_core_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| coarse->medium (info) | surface_change | C1 | F36_dinv_0_3mm | 24 | +0.04311 | +0.04191 | +0.001205 | 2.88 % | 0.02 | False |
| coarse->medium (info) | surface_inventory | C1 | F36_inv_0_3mm | 24 | +0.11177 | +0.11065 | +0.001119 | 1.01 % | 0.02 | True |
| coarse->medium (info) | deep_change | C1 | F36_ddeep_10_40mm | 24 | +0.09517 | +0.09628 | -0.001117 | 1.16 % | 0.05 | True |
| coarse->medium (info) | bottom_salt | C1 | F36_bottom_salt_in_g | 24 | +0.45389 | +0.45304 | +0.000854 | 0.19 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | F36_down_salt_net_3mm_g | 24 | -0.14019 | -0.13989 | -0.000294 | 0.21 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | F36_down_salt_net_10mm_g | 24 | -0.28898 | -0.28782 | -0.001167 | 0.41 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | F36_down_salt_net_20mm_g | 24 | -0.38344 | -0.38099 | -0.002453 | 0.64 % | 0.05 | True |
| coarse->medium (info) | core_descending_vf | C1 | F36_core_desc_vf_1e-8 | 24 | +0.08295 | +0.16859 | -0.085634 | 50.80 % | 0.05 | False |
| coarse->medium (info) | surface_change | C1 | W3_dinv_0_3mm | 24 | +0.10457 | +0.10522 | -0.000653 | 0.62 % | 0.02 | True |
| coarse->medium (info) | surface_inventory | C1 | W3_inv_0_3mm | 24 | +0.16636 | +0.16709 | -0.000730 | 0.44 % | 0.02 | True |
| coarse->medium (info) | deep_change | C1 | W3_ddeep_10_40mm | 24 | +0.05553 | +0.05465 | +0.000879 | 1.61 % | 0.05 | True |
| coarse->medium (info) | bottom_salt | C1 | W3_bottom_salt_in_g | 24 | +0.02148 | +0.02155 | -0.000066 | 0.31 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | W3_down_salt_net_3mm_g | 24 | -0.00749 | -0.00724 | -0.000257 | 3.56 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | W3_down_salt_net_10mm_g | 24 | -0.03570 | -0.03584 | +0.000141 | 0.39 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C1 | W3_down_salt_net_20mm_g | 24 | -0.03705 | -0.03747 | +0.000416 | 1.11 % | 0.05 | True |
| coarse->medium (info) | core_descending_vf | C1 | W3_core_desc_vf_1e-8 | 24 | +0.00000 | +0.00000 | +0.000000 | – | – |  |
| coarse->medium (info) | interface_net | C1 | iface_salt_net_g | 24 | +0.25679 | +0.25708 | -0.000298 | 0.12 % | 0.05 | True |
| coarse->medium (info) | interface_pos | C1 | iface_salt_pos_g | 24 | +0.29175 | +0.29275 | -0.001006 | 0.34 % | 0.05 | True |
| coarse->medium (info) | interface_liquid_net | C1 | iface_liquid_net_mL | 24 | +3.64990 | +3.64681 | +0.003097 | 0.08 % | 0.05 | True |
| coarse->medium (info) | surface_change | C0 | F36_dinv_0_3mm | 24 | +0.05044 | +0.04923 | +0.001218 | 2.47 % | 0.02 | False |
| coarse->medium (info) | surface_inventory | C0 | F36_inv_0_3mm | 24 | +0.11910 | +0.11797 | +0.001132 | 0.96 % | 0.02 | True |
| coarse->medium (info) | deep_change | C0 | F36_ddeep_10_40mm | 24 | +0.11522 | +0.11792 | -0.002700 | 2.29 % | 0.05 | True |
| coarse->medium (info) | bottom_salt | C0 | F36_bottom_salt_in_g | 24 | +0.24022 | +0.24024 | -0.000012 | 0.00 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | F36_down_salt_net_3mm_g | 24 | -0.05044 | -0.04923 | -0.001218 | 2.47 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | F36_down_salt_net_10mm_g | 24 | -0.12500 | -0.12231 | -0.002688 | 2.20 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | F36_down_salt_net_20mm_g | 24 | -0.19613 | -0.19413 | -0.001999 | 1.03 % | 0.05 | True |
| coarse->medium (info) | core_descending_vf | C0 | F36_core_desc_vf_1e-8 | 24 | +0.22789 | +0.22057 | +0.007318 | 3.32 % | 0.05 | True |
| coarse->medium (info) | surface_change | C0 | W3_dinv_0_3mm | 24 | +0.10014 | +0.10091 | -0.000768 | 0.76 % | 0.02 | True |
| coarse->medium (info) | surface_inventory | C0 | W3_inv_0_3mm | 24 | +0.16193 | +0.16277 | -0.000846 | 0.52 % | 0.02 | True |
| coarse->medium (info) | deep_change | C0 | W3_ddeep_10_40mm | 24 | +0.03580 | +0.03461 | +0.001189 | 3.44 % | 0.05 | True |
| coarse->medium (info) | bottom_salt | C0 | W3_bottom_salt_in_g | 24 | +0.23674 | +0.23664 | +0.000101 | 0.04 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | W3_down_salt_net_3mm_g | 24 | -0.10014 | -0.10091 | +0.000769 | 0.76 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | W3_down_salt_net_10mm_g | 24 | -0.20094 | -0.20203 | +0.001089 | 0.54 % | 0.05 | True |
| coarse->medium (info) | vertical_transport | C0 | W3_down_salt_net_20mm_g | 24 | -0.23216 | -0.23253 | +0.000375 | 0.16 % | 0.05 | True |
| coarse->medium (info) | core_descending_vf | C0 | W3_core_desc_vf_1e-8 | 24 | +0.00000 | +0.00000 | +0.000000 | – | – |  |
| coarse->medium (info) | effect | E=C1-C0 | F36_inv_0_3mm | 24 | -0.00733 | -0.00732 | -0.000013 | 0.18 % | 0.02 | True |
| coarse->medium (info) | effect | E=C1-C0 | F36_inv_0_2mm | 24 | -0.00502 | -0.00503 | +0.000018 | 0.37 % | 0.02 | True |
| coarse->medium (info) | effect | E=C1-C0 | F36_ddeep_10_40mm | 24 | -0.02006 | -0.02164 | +0.001583 | 7.32 % | 0.05 | False |
| coarse->medium (info) | effect | E=C1-C0 | F36_bottom_salt_in_g | 24 | +0.21367 | +0.21280 | +0.000866 | 0.41 % | 0.05 | True |
| coarse->medium (info) | effect | E=C1-C0 | W3_inv_0_3mm | 24 | +0.00443 | +0.00431 | +0.000115 | 2.67 % | 0.02 | False |
| coarse->medium (info) | effect | E=C1-C0 | W3_inv_0_2mm | 24 | +0.00270 | +0.00261 | +0.000091 | 3.48 % | 0.02 | False |
| coarse->medium (info) | effect | E=C1-C0 | W3_ddeep_10_40mm | 24 | +0.01973 | +0.02004 | -0.000311 | 1.55 % | 0.05 | True |
| coarse->medium (info) | effect | E=C1-C0 | W3_bottom_salt_in_g | 24 | -0.21526 | -0.21509 | -0.000167 | 0.08 % | 0.05 | True |
| coarse->medium (info) | onset | C1 | onset_F36_all_thr1.0e-08 | - | +6.83333 | +6.66667 | +0.166667 | – | 10 min | True |
| coarse->medium (info) | onset | C1 | onset_F36_core_thr1.0e-08 | - | 10.5 | 10.2 | +0.333333 | – | 10 min | False |
| coarse->medium (info) | onset | C1 | onset_W3_all_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| coarse->medium (info) | onset | C1 | onset_W3_core_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| coarse->medium (info) | onset | C0 | onset_F36_all_thr1.0e-08 | - | 14 | 14 | +0.000000 | – | 10 min | True |
| coarse->medium (info) | onset | C0 | onset_F36_core_thr1.0e-08 | - | 14.5 | 14.2 | +0.333333 | – | 10 min | False |
| coarse->medium (info) | onset | C0 | onset_W3_all_thr1.0e-08 | - | – | – | – | – | 10 min | True |
| coarse->medium (info) | onset | C0 | onset_W3_core_thr1.0e-08 | - | – | – | – | – | 10 min | True |
