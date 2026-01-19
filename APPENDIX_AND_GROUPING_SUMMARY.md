# 附录覆盖与图表分组功能总结

## 已实施的改进

### 1. 附录覆盖（Appendix Coverage）

#### 结构要求升级
- **之前**：IMRAD (Introduction, Methods, Results, Discussion)
- **现在**：IMRAD + Appendix/Supplementary

#### 明确要求
- 附录中的所有图表（Supplementary Figure, Figure S1, Table S1等）都必须分析
- 附录中的公式、算法、详细推导都要创建对应section

#### 示例层级
```
6. 附录分析 (Appendix/Supplementary)
├─ 6.1 Figure S1-S2: 补充实验数据
└─ 6.2 详细算法推导
```

### 2. 图表分组策略（Figure Grouping）

#### 分组原则
- **单个图表**：独立section（如 "3.1.1 Fig 1: 任务范式"）
- **相关图表组**：1-3个相关图表合并（如 "3.1.1 图表组: Fig 1-3 (实验设计)"）
- **分组criteria**：相同主题、相同部分、或紧密相关
- **层级位置**：作为对应部分的子section

#### 示例结构
```
3. 实验设计 (Methods)
├─ 3.1 实验范式与刺激
│  ├─ 3.1.1 图表组: Fig 1-2 (任务流程与刺激设计)
│  └─ 3.1.2 Equation 1-2: logLR计算
└─ 3.2 数据分析
    └─ 3.2.1 Figure 3: 统计方法流程图

4. 结果 (Results)
└─ 4.1 行为数据
    └─ 4.1.1 Fig 3-5 (准确率、反应时、学习曲线)
```

### 3. 增强的覆盖检查

#### 更新的自检清单
- [x] 图表清单中的每个图/表是否都有对应的section（**包括Supplementary Figures**）？
- [x] 每个编号公式（如果有）是否都被分析（**包括附录中的公式**）？
- [x] 每个figure/equation类型的section的第一个问题是否回答了"是什么+原理"？
- [x] IMRAD四大部分是否都有覆盖？
- [x] **如果论文有附录/补充材料，是否为其创建了分析section？**
- [x] **相关图表是否合理分组（1-3个为一组）作为对应部分的子section？**
- [x] 每个section的sub_questions是否包含2-4个不同类型的问题？

## 预期效果

### 之前可能遗漏的
- ❌ Supplementary Figures未分析
- ❌ 附录中的公式被忽略
- ❌ 每个图表单独一个section（过于分散）

### 现在的改进
- ✅ 附录内容完整覆盖
- ✅ 相关图表分组，结构更清晰
- ✅ 层级关系明确（作为对应部分的子section）

## 使用说明

分析时会自动应用这些改进，Architect会：
1. 检查是否有附录/补充材料
2. 将相关图表分组（1-3个为一组）
3. 作为对应部分（Methods/Results等）的子section创建
4. 确保所有附录内容不被遗漏
