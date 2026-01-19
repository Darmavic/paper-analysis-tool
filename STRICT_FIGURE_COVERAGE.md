# 严格图表覆盖与优先问题验证总结

## 新的严格要求

### 1. 强制覆盖所有图表
- ✅ **所有** figure、table、equation必须有对应的子section分析
- ✅ equation可以1-3个为一组放到一个section里
- ✅ 验证直到合格为止

### 2. 优先问题拆分（重大变化）

#### 之前
- 1个合并问题："是什么+原理"
- 类型：phenomenon
- 字数：1000-3000字

#### 现在
**两个独立问题**：

**问题1 - 是什么**
- 类型：`what`
- 内容：描述图表/公式的内容、元素、符号含义
- 输出要求：600-2000字
- 验证标准：500-3000字

**问题2 - 原理**
- 类型：`principle`
- 内容：解释工作原理、推导逻辑、理论基础
- 输出要求：600-2500字
- 验证标准：500-3500字

### 3. 验证机制

#### 自动验证流程
1. **Architect生成后**：检查每个figure/equation section
2. **检查条件**：前两个问题是否为'what'和'principle'类型
3. **自动补全**：如缺失，自动生成两个独立问题
4. **字数验证**：分析时分别验证'what'和'principle'的字数

#### 预期输出
```
✅ 优先问题验证通过: 所有figure/equation section都包含'是什么'和'原理'两个优先问题
```

或：
```
🔧 自动补充优先问题: 3.1.1 Fig 1分析 (是什么+原理)
✅ 优先问题验证完成: 自动补充了3个section的优先问题（每个包含'是什么'+'原理'两个问题）
```

## 示例结构

### Figure Section
```json
{
  "section_title": "3.1.1 Fig 1: 任务范式",
  "type": "figure",
  "sub_questions": [
    {
      "question": "Fig 1展示了什么内容？图中各个元素...",
      "question_type": "what"  // 600-2000字
    },
    {
      "question": "Fig 1的工作原理/流程是怎样的？...",
      "question_type": "principle"  // 600-2500字
    },
    {
      "question": "该设计如何确保...",
      "question_type": "mechanism"
    },
    {
      "question": "如果改变...",
      "question_type": "critique"
    }
  ]
}
```

### Equation Section
```json
{
  "section_title": "3.2.1 Equation 1-2: logLR计算",
  "type": "equation",
  "sub_questions": [
    {
      "question": "Equation 1-2的完整数学表达式是什么？...",
      "question_type": "what"  // 600-2000字
    },
    {
      "question": "Equation 1-2的推导逻辑和计算原理是怎样的？...",
      "question_type": "principle"  // 600-2500字
    },
    {
      "question": "这些公式的理论基础...",
      "question_type": "mechanism"
    }
  ]
}
```

## 实施的修改

1. **SubQuestion模型**：添加'what'和'principle'类型及对应字数限制
2. **validate_and_fix_priority_questions**：改为生成两个独立问题
3. **Architect提示词**：明确要求两个独立问题，不能合并
4. **覆盖检查清单**：验证前两个问题类型

## 优势

- ✅ **更严格的保证**：每个图表必有"是什么"和"原理"两部分
- ✅ **字数可控**：分别验证，避免一个问题过长或过短
- ✅ **结构清晰**：分析时明确知道哪部分是描述，哪部分是原理
- ✅ **100%覆盖**：自动补全机制确保不遗漏
