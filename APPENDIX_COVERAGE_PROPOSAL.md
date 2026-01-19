# 附录覆盖改进方案

## 发现的问题

当前Architect提示词中：
- ✅ 有 `appendix_instruction`（是否分析附录的开关）
- ❌ 缺少对附录内容的具体要求
- ❌ 附录中的补充图表/公式可能被忽略

## 建议改进

### 1. 在"第二优先级：IMRAD结构完整性"中添加附录

**现在**：
```
### 第二优先级：IMRAD结构完整性
1. {appendix_instruction}
2. **结构自检**: 你的大纲必须完整覆盖学术论文的核心结构 (IMRAD: Introduction, Methods, Results, Discussion)。
```

**改进后**：
```
### 第二优先级：IMRAD + Appendix 结构完整性
1. {appendix_instruction}
2. **结构自检**: 你的大纲必须完整覆盖学术论文的核心结构：
   - IMRAD: Introduction, Methods, Results, Discussion
   - **Appendix/Supplementary**: 如果论文包含附录或补充材料，必须为其创建专门的section
3. **附录要求**：
   - 附录中的所有图表（Supplementary Figure, Figure S1等）都必须单独分析
   - 附录中的公式、算法、详细推导都要创建对应section
```

### 2. 在标号规范示例中添加附录

**添加示例**：
```
- `6. 附录分析 (Appendix)`
- `6.1 Figure S1: 补充实验数据`
- `6.2 详细算法推导`
```

### 3. 在覆盖完整性清单中添加附录检查

**现在**：
```
- [ ] 图表清单中的每个图/表是否都有对应的section？
- [ ] 每个编号公式（如果有）是否都被分析？
- [ ] **每个figure/equation类型的section的第一个问题是否回答了"是什么+原理"？**
- [ ] IMRAD四大部分是否都有覆盖？
```

**改进后**：
```
- [ ] 图表清单中的每个图/表是否都有对应的section（包括Supplementary Figures）？
- [ ] 每个编号公式（如果有）是否都被分析（包括附录中的公式）？
- [ ] **每个figure/equation类型的section的第一个问题是否回答了"是什么+原理"？**
- [ ] IMRAD四大部分是否都有覆盖？
- [ ] 如果有附录，是否为附录创建了分析section？
```

## 实施方式

### 方式1：修改Prompt（推荐）
直接修改提示词，明确要求分析附录

### 方式2：修改Figure Scanner
让FigureScanner也扫描附录页，确保补充图表被检测

### 方式3：两者结合
既修改提示词，又扩展扫描范围

## 建议

**优先修改Prompt**，因为：
1. 改动最小
2. 立即生效
3. 不需要修改扫描逻辑

**是否需要我实施这个改进？**
