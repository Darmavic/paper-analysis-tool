# 公式检测改进总结

## 问题诊断

### 用户论文情况
- **论文**：41_RNNs_reveal_a_new_optimal_s.pdf
- **公式数量**：20个编号公式
- **位置**：第8-14页
- **格式**：独立编号 (1), (2)...(20)

### 为什么之前没有公式section？

1. **FigureScanner不扫描公式**
   - 只扫描figures和tables
   - 不传公式清单给Architect

2. **Architect依赖清单**
   - 如果清单中没有公式信息
   - 可能不主动从文本中识别

3. **公式格式多样**
   - "Equation 1", "Eq. 2", "(1)", "(2)"
   - 需要明确告诉Architect扫描这些模式

## 解决方案

### 已实施：增强Architect提示词

#### 新增"公式主动扫描"要求
```
3. **公式主动扫描**：⚠️ 重要！你必须**主动扫描文本**寻找编号公式：
   - 寻找模式："Equation 1", "Eq. 2", 或独立编号如"(1)", "(2)"...
   - Marker已将公式转换为LaTeX格式（$$...$$），编号通常在公式下方或旁边
   - 为每组1-3个相关公式创建分析section（如"3.2.1 Equation 1-3: 计算公式"）
   - **即使图表清单中没有公式，也要扫描文本！**
```

#### 更新检查清单
```
- [ ] **已主动扫描文本，是否为所有编号公式创建了equation section（包括附录）？**
```

## 预期效果

### 之前
- ❌ 没有equation sections
- ❌ 20个公式未被分析

### 现在
- ✅ Architect主动扫描文本
- ✅ 识别 (1), (2)...(20) 编号
- ✅ 创建equation sections（可1-3个分组）
- ✅ 每个equation section包含'what'和'principle'两个优先问题

## 示例输出

预期生成section如：
```
3.2 理论推导 (Theory)
├─ 3.2.1 Equation 1-5: RNN损失函数
│  ├─ (what) 这些公式的数学表达式是什么？
│  └─ (principle) 推导逻辑是怎样的？
└─ 3.2.2 Equation 6-10: 优化算法
   ├─ (what) 公式定义了什么？
   └─ (principle) 计算原理是什么？
```

## 验证步骤

1. **重新运行分析**：用新提示词分析41_RNNs论文
2. **检查结果**：是否出现equation sections
3. **确认覆盖**：是否涵盖所有20个公式

## 备用方案

如果Architect仍无法识别，可以：
1. 添加EquationScanner类
2. 从Marker输出中提取LaTeX公式
3. 构建公式清单传给Architect
