# v17 磁盘审计与输出降采样交付

本目录是 `task/2.md` 的轻量、可审计交付。它不包含约 0.904 GiB 的稀疏 VTU 工作副本、短回归原始 VTU、求解二进制或多 GB 全分辨率归档；这些大文件仍由项目端的哈希清单和独立备份管理。

## 结论

- 审计期间没有删除任何原始场、归档、失败记录，也没有中断或修改活动 3D G3。
- 已完成案例在 Frodo 上的压缩场约 38.323 GiB，只有在重新核验本地全量归档、稀疏工作集、后处理和精确删除清单后，才可作为第一阶段远端清理候选。
- 保留 600 s 数值检查点，但令 `Benchmark.VtkEvery=6` 可将完整场降为每小时一次；短回归中 VTU+PVD 字节减少 71.13%，所有 24 个终态数组和四类守恒表严格零差。
- 新增的逐接受步 1 mm 粗/细砂紧凑剖面通过非扰动门槛：终态浓度与完整 VTK 回算最大差 `9.55e-15 M`。

## 阅读顺序

1. [磁盘用量审计](DISK_USAGE_AUDIT.md)
2. [安全归档与清理提案](SAFE_ARCHIVE_AND_CLEANUP_PLAN.md)
3. [输出降采样实现](OUTPUT_REDUCTION_IMPLEMENTATION.md)
4. [原始/降采样/紧凑剖面等价性](OUTPUT_EQUIVALENCE_TEST.md)

机器可读证据包括 `regression/equivalence_results.json`、`regression/profile_overlay_equivalence.json`、PVD/VTK 读取验证、容量门槛结果、稀疏工作集索引和 `EVIDENCE_MANIFEST.json`。`source_overlay/` 是未来计算候选，不会追溯修改冻结 v13 结果。

## 证据边界

短窗零差证明输出频率和诊断写入在该回归中未扰动数值解；它不是新的网格或时间步收敛研究，也不是底部边界或实验现象的物理验证。Frodo 的 `pvpython` 代理创建崩溃、sal 的 ParaView Python 模块缺失，因此这里只声称 PVD 与 VTK XML 读取通过，不虚报 GUI/代理验证通过。
