# 公式识别问题分析

## Marker的公式识别能力

### ✅ Marker能做什么
- 识别PDF中的数学公式
- 转换为LaTeX格式（`$inline$` 或 `$$display$$`）
- 保留在转换后的markdown文本中

### ❌ 当前为什么没有公式section

#### 原因1：Architect依赖编号
- Architect只会为**明确编号的公式**创建section
- 需要文本中出现："Equation 1", "Eq. 2", "公式(1)"等标记
- 如果论文只有：
  - 内嵌公式（inline math）
  - 未编号的显示公式
- Architect不会创建专门section

#### 原因2：FigureScanner不扫描公式
- 当前`FigureScanner`只扫描figures和tables
- 不扫描equations
- 图表清单中没有公式信息

## 解决方案

### 方案1：强化Architect提示词（简单）
- 明确要求扫描文本中的"Equation X"标记
- 即使图表清单中没有，也要识别

### 方案2：扩展FigureScanner（完整）
- 添加equation扫描功能
- 自动提取编号公式清单
- 传给Architect确保覆盖

### 方案3：检查Marker输出（验证）
- 查看转换后的文本是否包含LaTeX
- 确认Marker识别正常工作

## 需要验证

1. **您分析的论文中是否有编号公式？**
   - 如果有：需要改进Architect检测
   - 如果没有：当前行为正确

2. **Marker输出中是否包含LaTeX？**
   - 检查文本中是否有 `$...$` 或 `$$...$$`
   - 确认公式识别正常

## 下一步

等待用户确认：
- 论文名称
- 是否应该有公式section
- 查看Marker输出示例
