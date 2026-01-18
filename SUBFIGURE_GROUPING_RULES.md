# 子图自动分组规则

## 核心规则

### 优先规则1：子图必须分组
如果检测到相同主图编号的多个子图（如 Fig 1a, Fig 1b, Fig 1c），**必须合并**为一个section。

#### 适用范围
- `Fig Xa, Xb, Xc...` → `Fig Xa-c`
- `Figure S1a, S1b, S1c...` → `Figure S1a-c`
- `Table 1a, 1b, 1c...` → `Table 1a-c`
- 所有带子编号（a, b, c, d...）的图表

#### 标题格式
```
"3.1.1 Fig 1a-c: 实验范式的三个条件"
"4.1.1 Fig 3a-d: 准确率分析的四个视角"
"6.1 Figure S1a-b: 补充实验数据"
```

### 优先规则2：公式可选分组
1-3个相关公式（连续推导步骤）可以合并：
```
"3.2.1 Equation 1-3: logLR计算步骤"
```

### 一般规则3：主题相关可选分组
不同主图但主题紧密相关的可以合并（1-3个）：
```
"4.1.2 Fig 4-5: 反应时与学习曲线"
```

## 示例对比

### ❌ 错误：子图分开
```json
[
  {
    "section_title": "3.1.1 Fig 1a: 条件A",
    "type": "figure"
  },
  {
    "section_title": "3.1.2 Fig 1b: 条件B",
    "type": "figure"
  },
  {
    "section_title": "3.1.3 Fig 1c: 条件C",
    "type": "figure"
  }
]
```

### ✅ 正确：子图合并
```json
[
  {
    "section_title": "3.1.1 Fig 1a-c: 实验范式的三个条件",
    "type": "figure",
    "target_pages": [2, 3],
    "sub_questions": [
      {
        "question": "Fig 1a-c分别展示了什么内容？三个子图中的元素分别代表什么含义？",
        "question_type": "what"
      },
      {
        "question": "Fig 1a-c展示的三个条件如何共同构成完整的实验范式？其工作原理是怎样的？",
        "question_type": "principle"
      },
      ...
    ]
  }
]
```

## 优势

1. ✅ **避免碎片化**：不会为每个subfigure创建独立section
2. ✅ **保持逻辑**：子图作为整体呈现，便于理解其相互关系
3. ✅ **减少冗余**：一个section分析整组subfigures，避免重复相似内容
4. ✅ **符合习惯**：多数论文中subfigures本就是一个整体

## 实施方式

### Architect提示词
已在"图表分组原则"中明确：
- **优先规则1**：相同主图的子图**必须**合并
- 提供多个示例（Fig 1a-c, Fig S1a-b等）
- 标题格式明确（Fig Xa-z: 描述）

### 自动识别
LLM会自动识别子图编号模式：
- 相同数字 + 字母后缀 → 自动分组
- 检测到 Fig 1a, 1b → 合并为 Fig 1a-b

## 注意事项

- **target_pages**：包含所有子图所在的页码
- **问题设计**：涵盖所有子图，不遗漏任何一个
- **描述性标题**：说明这组子图的共同主题
