# Heterogeneity: RH=0 cylinder evaporation and salt precipitation

本仓库归档 RH=0、固定孔隙率和本征渗透率的三维圆柱计算，包括等温 **v12 / 174 h** 对照、独立验收的非等温 **v13 / 174 h** 结果、气膜厚度部分率定记录，以及本研究分支的底部边界敏感性计算和L1粗砂浓度偏差审计。各数据集分别标注完整、部分和用户终止状态；数值匹配不等同于独立物理验证，原v12交付目录保持不变。

## v13 底部边界敏感性计算（进行中）

依据 `bottom boundary.md` 新增独立非等温 v13 计算：B0–B3 等效滤板阻力，G1–G3 显式4.5mm滤板与2/5/10mm中心入口。几何尺寸与滤板物性是注明的探索假设，不是已测量材料参数。

- [计算说明与复现边界](model_revisions/20261103_v13_bottom_boundary_campaign/README.md)
- [基准验收](model_revisions/20261103_v13_bottom_boundary_campaign/BASELINE_VERIFICATION.md) / [边界实现](model_revisions/20261103_v13_bottom_boundary_campaign/BOUNDARY_IMPLEMENTATION.md)
- [作业状态快照](model_revisions/20261103_v13_bottom_boundary_campaign/RUN_STATUS.csv) / [比较状态](model_revisions/20261103_v13_bottom_boundary_campaign/FINAL_COMPARISON.md)

原网格短窗零改动回归与G组供体/热通量测试已通过；B短程验收在sal运行，174h作业等待依赖，G动力学验收等待可用资源。尚无新174h结果，不声称边界修改改善试验符合度。旧审计、v12/v13已接受结果保留；本研究分支不合并main。

## L1 粗砂浓度偏差审计（独立研究分支）

- [最终诊断](analysis/coarse_174h_diagnosis/FINAL_DIAGNOSIS.md) / [六页图件 PDF](analysis/coarse_174h_diagnosis/results/COARSE_174H_AUDIT_FIGURES.pdf)
- [Phase 1 发现](analysis/coarse_174h_diagnosis/PHASE_1_FINDINGS.md) / [后续受控试验矩阵](analysis/coarse_174h_diagnosis/SENSITIVITY_MATRIX.md)
- [来源、复现与校验说明](analysis/coarse_174h_diagnosis/README.md)

完成了 MRI 来源审计、1044 帧原生面通量回放、粗细砂盐量闭合及独立热效应比较。回放不推进求解时间；未新增174 h物理敏感性计算。诊断明确区分模型输运机制、待检验的边界假设及实验观测不确定性。本分支不自动合并 main。
## 阅读入口

- [完整中文分析报告](deliveries/RH0_fixed_174h_20261103/model_revisions/20261102_cylinder_fixed_hydraulics_v12/FIXED_HYDRAULICS_174H_REPORT.md)
- [八页图件 PDF](deliveries/RH0_fixed_174h_20261103/model_revisions/20261102_cylinder_fixed_hydraulics_v12/results/comparison/RH0_FIXED_174H_COMPARISON.pdf)
- [蒸发曲线](deliveries/RH0_fixed_174h_20261103/model_revisions/20261102_cylinder_fixed_hydraulics_v12/results/comparison/01_evaporation.png)、[浓度剖面](deliveries/RH0_fixed_174h_20261103/model_revisions/20261102_cylinder_fixed_hydraulics_v12/results/comparison/03_profiles.png)、[粗砂下沉](deliveries/RH0_fixed_174h_20261103/model_revisions/20261102_cylinder_fixed_hydraulics_v12/results/comparison/04_downflow.png)
- [仅依据称重速率的阶段变化分析](deliveries/RH0_fixed_174h_20261103/analysis/evaporation_only_onset_20261102/EVAPORATION_ONLY_INFERENCE.md)
- [完整ZIP交付包](archives/RH0_fixed_174h_analysis_20261103.zip) / [SHA256](archives/RH0_fixed_174h_analysis_20261103.zip.sha256)
- [非等温v13及气膜率定交付说明](deliveries/RH0_nonisothermal_20261104/README.md)
- [非等温8.10 mm完整174 h报告](deliveries/RH0_nonisothermal_20261104/model_revisions/20261102_cylinder_thermal_v13/COMPLETION_REPORT.md)
- [7.5/8.0/8.10 mm蒸发曲线比较](deliveries/RH0_nonisothermal_20261104/analysis/film_7p5_8p0_8p1_snapshot_20261104/evaporation_comparison.pdf)
- [v17磁盘审计与输出降采样交付](deliveries/output_reduction_v17_20261104/README.md)：含安全清理提案、每小时场输出实现、PVD驱动后处理及严格短窗等价性证据；尚未执行原始数据删除。

## 主要结果与限制

- 已完成2 h预平衡及174 h蒸发，终态数值验收、原始备份与视觉检查通过。
- 1–174 h储液器溶液失重：模型57.216967 g，试验51.52 g，偏差+11.0578%；区间速率加权RMSE为0.040368 g/h。该量与顶面纯水蒸发通量分别处理。
- 关闭固盐对孔隙率/K的反馈使计算越过旧65.28 h失效点，但共同时间窗的蒸发、浓度和下沉结果几乎未变，不能称整体匹配改善。
- 174 h粗/细砂内部3–37 mm浓度RMSE分别为1.223719/0.205039 mol/L；模型后期粗砂浓度明显偏低。
- 最终固盐0.373802 g，均在细砂。最大等效固盐体积变量10.9767仅用于库存诊断，不代表几何孔隙占据或真实盐壳。
- 57.5833 h是模型首个接受步平衡析盐事件。称重速率分析的40–60 h只是条件性阶段变化候选，不能当作已验证实验结晶时间。
- 未完成新增全时窗网格/时间步收敛；数值守恒不等于物理验证。未使用MRI浓度或章稿96–108 h窗口推断实验结晶起始。

## 数据和复现

`deliveries/RH0_fixed_174h_20261103/`保持原项目相对路径，包含报告、图件、CSV、提取场NPZ、分析代码、v12覆盖源码/输入及验收来源。完整原始VTU、二进制和DuMuX/DUNE依赖不在此仓库；本仓库是分析交付，不是完整求解环境。

```bash
cd deliveries/RH0_fixed_174h_20261103
python verify_package.py
python model_revisions/20261102_cylinder_fixed_hydraulics_v12/finalize_compare.py
python model_revisions/20261102_cylinder_fixed_hydraulics_v12/write_final_report.py
```

复算图件应在工作副本进行，会更新该副本中的结果。Python依赖版本见`PYTHON_ENVIRONMENT.json`。已在独立副本复算，五份关键数值输出逐字节一致，证据见[复算记录](archives/RH0_fixed_174h_analysis_20261103_reproduction.json)。

## 交付来源

交付日期：2026-11-03（Europe/Berlin）。本仓库由用户指定为提交目标。`deliveries`和ZIP内的文件保持打包时原字节，因此其中“尚未指定外部提交目标”等状态属于**打包时历史快照**，不代表本仓库的当前提交状态；当前提交以Git历史为准。

ZIP SHA256：`5e52ceecc2de9b01972ee465ac0481581226ebdf70dd366a9f108d0e648dc007`。

模型验收和备份由确定性脚本完成，Sonnet因组织403未能独立评审。未添加项目内容的开放许可；实验数据和依赖的来源/使用条件应按各自原始来源核对。
