# RH=0固定孔隙率与渗透率：174 h分析交付包

日期：2026-11-03（Europe/Berlin）。范围：本对话已完成的v12等温RH=0固定孔隙率/本征渗透率对照，以及仅依据原始称重速率的阶段变化分析。v13非等温、v14性能及Frodo厚度率定不属于本包结论。

## 先看这三份文件

1. [174 h完整中文报告](model_revisions/20261102_cylinder_fixed_hydraulics_v12/FIXED_HYDRAULICS_174H_REPORT.md)
2. [八页对比图PDF](model_revisions/20261102_cylinder_fixed_hydraulics_v12/results/comparison/RH0_FIXED_174H_COMPARISON.pdf)
3. [只用称重速率的阶段变化分析](analysis/evaporation_only_onset_20261102/EVAPORATION_ONLY_INFERENCE.md)及[配图](analysis/evaporation_only_onset_20261102/EVAPORATION_ONLY_CHANGEPOINT.pdf)

## 本次结论

- 实际174 h完成，数值验收及1369份备份校验通过；1057个原始场文件曾逐个解压核验。此处归档验收记录，不将数值闭合等同于物理验证。
- 1–174 h储液器溶液失重：模拟57.216967 g、试验51.52 g，偏高11.0578%；区间速率加权RMSE0.040368 g/h。该观测量与样品顶面纯水蒸发量分别处理。
- 关闭孔隙/K反馈后共同时间窗蒸发和粗砂下沉曲线几乎未变。174 h粗/细砂内部3–37 mm浓度RMSE分别为1.223719/0.205039 mol/L，粗砂浓度明显偏低，不能宣称整体匹配改善。
- 首个接受步固盐为57.5833 h，首个保存场为57.6667 h；最终0.373802 g固盐均位于细砂。等效固盐库存体积最大10.9767，只作库存诊断，不能解释为真实几何孔隙占据或盐壳。
- 只依据称重速率得到的40–60 h是依赖窗口/拟合形式的阶段变化候选，不是已验证结晶时间，未使用MRI或章稿96–108 h推定实验起始。

## 结构与证据

保留原项目相对路径，报告内链接可直接打开。`results/comparison`含8页图件、CSV指标、固定/耦合模型降维场NPZ、源哈希、终态验收和视觉QA；`source/inputs/tests`为v12模型覆盖源码、输入和测试来源。旧耦合模型仅比较实际接受到65.28 h的前缀，v06仅作24 h历史均匀蒸发参考。

本包不含数GB原始VTU、求解器二进制或完整DuMuX/DUNE依赖；它是分析结果交付包，不是完整求解环境。原场档仍保留在项目v12的`remote_backup`，原始场与备份清单中的路径指向原工作区/远端，不能将其文件数误当成本包文件数。包内`PACKAGE_MANIFEST.json`才是本次交付文件清单。

模型材料参数、网格、冻结二进制SHA、修复记录见METHOD、build_manifest和REPAIR_LOG。Sonnet组织403导致其未完成评审；不宣称已通过独立Claude审阅。没有改动其他模型、继续计算或重新率定。

## 复算分析

从解压包根目录运行（建议先复制到工作副本；绘图会更新该副本的产物）：

```powershell
python -X utf8 model_revisions/20261102_cylinder_fixed_hydraulics_v12/finalize_compare.py
python -X utf8 model_revisions/20261102_cylinder_fixed_hydraulics_v12/write_final_report.py
```

上述代码使用已提取NPZ与预算CSV，绘制八页图并重算指标。旧v06/v03模块仅导入其绘图/读取辅助函数，不执行其历史主流程。`finalize_extract.py`是原场解压校验/提取来源，需恢复外部完整原场档才能运行，不属于本包可独立执行的步骤。

阶段变化分析可运行`analysis/evaporation_only_onset_20261102/analyze.py`，只读取matched_mass.csv中的time_h/mass_g；`plot_report.py`重绘该分析图（原脚本字体路径适用Windows）。Python库版本记录于`PYTHON_ENVIRONMENT.json`，字体和绘图库版本可能改变图的字节哈希，故复算比较数值指标而不是PDF哈希。

验证解压包未损坏：

```powershell
python verify_package.py
```

## 提交状态

本包完成本地整理交付。原项目根目录不是Git仓库；尚未指定外部仓库、平台或共享目录，因此没有执行Git提交、推送或外部上传。包内原始DELIVERY_STATUS表示分析准备状态，不代表外部提交回执。
