### 使用指南
**请复制以下内容发送给 AI 助手：**

> “我需要开发一个自动化的论文分析工具。请阅读以下技术规格说明书，特别是关于‘Hub & Spoke’架构、多模态分析逻辑以及 Prompt 设计的部分。请根据此文档一步步为我编写 Python 代码。”

---

# 项目规格说明书：论文到 Obsidian 智能分析工作流 (Paper-to-Obsidian Workflow)

## 1. 项目概述
本项目旨在开发一个自动化工具，能够读取学术 PDF 论文，并在 Obsidian 中生成结构化、互相关联的知识库。该工具利用 **多模态大模型 (Multimodal LLM, 如 GPT-4o)** 对论文中的图表、公式和文本进行视觉分析，并自动构建“中心-分支 (Hub & Spoke)”式的笔记结构。

### 核心设计理念
- **Hub (中心节点/主索引):** 一个总览页面，包含论文摘要和结构化的问题树索引。
- **Spoke (分支节点/详情页):** 针对特定问题、图表或公式的原子化笔记，与中心节点进行双向链接。
- **逻辑 + 风格 (Logic + Style):** 分析过程必须遵循严格的**思维框架 (Framework)**，同时输出结果需模仿特定的**问答风格 (Few-Shot)**。

## 2. 技术栈
- **编程语言:** Python 3.9+
- **PDF 处理:** `PyMuPDF (fitz)` (用于将页面渲染为高清图片，这对 AI 识别公式至关重要)。
- **AI 模型:** `Google Gemini 1.5 Pro` (使用 `google-generativeai` 库，具备强大的原生多模态能力)。
- **数据结构:** `Pydantic` (用于规范数据输出)。
- **输出格式:** Markdown (`.md`)，适配 Obsidian 的语法（双链、LaTeX 公式）。

## 3. 数据架构与工作流

### 3.1 目录结构 (Obsidian Vault)
```text
C:/Users/55459/Desktop/Darmavic/组会/Decision making/26.1.14-26.1.20/
├── 论文标题文件夹/
│   ├── 00_Master_Index.md       # Hub: 主索引页
│   ├── assets/                  # 存放提取的图片 (可选)
│   ├── analysis_fig_3.md        # Spoke: 图3深度解析
│   ├── analysis_eq_4.md         # Spoke: 公式4推导解析
│   └── analysis_methodology.md  # Spoke: 方法论讨论
```

### 3.2 工作流管道 (Pipeline - implemented as a Skill)
本项目将封装为 Antigravity 的 **本地技能 (Local Skill)**，位于 `.agent/skills/paper_to_obsidian/`。
1.  **摄入 (Ingestion):** 读取 PDF -> 将每一页转换为高清图片 -> 提取基础文本（用于生成大纲）。
2.  **映射 (Agent A - 架构师):** 分析论文目录和摘要 -> 生成一份包含“深度研读问题”的列表 (JSON格式)。
3.  **推理 (Agent B - 分析师):** 遍历每个问题 -> 找到对应的 PDF 页码图片 -> 发送图片+提示词给 Gemini Pro -> 生成 Markdown 格式的深度问答。
4.  **链接 (Linking):** 组装文件，确保 `[[WikiLinks]]` 正确指向对应的文件名。

## 4. 详细组件规格

### 组件 A: PDF 处理器 (`pdf_engine.py`)
**功能:**
- 将 PDF 指定页码转换为 Base64 编码的图片（供 LLM 视觉输入）。
- 提取纯文本用于初步分析。

**核心函数签名:**
```python
def get_page_image(pdf_path: str, page_number: int) -> str:
    """返回该页面的 base64 编码字符串，dpi设置至少为300"""
    pass
```

### 组件 B: 架构师 Agent (主索引生成器)
**角色:** 阅读摘要和目录，构建学习地图。
**输出格式 (JSON Schema):**
```json
{
  "paper_title": "字符串",
  "summary": "字符串",
  "sections": [
    {
      "section_title": "结果分析 - Figure 3",
      "target_pages": [4, 5],
      "filename_slug": "analysis_fig_3",
      "type": "figure",
      "intent": "分析准确率随时间下降的原因及图表中的异常点。"
    }
  ]
}
```

### 组件 C: 分析师 Agent (深度解析核心)
**角色:** 这是核心逻辑。接收特定页面的图片和用户意图，生成内容。

**关键要求:** 必须结合 **思维链 (Chain-of-Thought)** 和 **少样本提示 (Few-Shot Prompting)**。

#### **Prompt 模板设计 (请在代码中严格实现):**

**System Prompt (系统提示词):**
```text
你是一个严谨的学术研究专家。你的目标是将复杂的论文片段拆解为清晰的“问题-答案”对。

## 思维框架 (必须遵循以下逻辑，但不要输出内心独白)
1. **视觉解码:** 扫描输入图片中的坐标轴、图例、显著性标记(*)或公式符号。
2. **上下文关联:** 将视觉数据与论文文本中的核心主张联系起来。
3. **批判性思维:** 识别数据中的局限性、反直觉的结果或作者的潜在假设。

## 输出格式
使用 Markdown 格式，数学公式使用 LaTeX 格式（包裹在 $...$ 中）。
```

**User Prompt (用户提示词 - 包含样本):**
```text
## 任务
分析目标: {intent}
参考页面: 见附图。

## 风格样本 (请务必模仿以下 Q&A 的语气和深度)
<Example 1: 针对图表分析>
Q: Fig 3 中，为什么在 t=200ms 时准确率出现了陡降？
A: 原文指出这是由于“干扰物呈现 (distractor onset)”造成的。这说明该模型对动态噪声极其敏感。
Q: 这里的宽误差棒 (Wide Error Bar) 意味着什么？
A: 这意味着在低信噪比条件下，不同受试者之间的个体差异显著扩大。

<Example 2: 针对公式分析>
Q: 公式(4)中引入参数 $\lambda$ 的物理意义是什么？
A: 这是一个正则化项，用于强制权重矩阵保持稀疏，防止过拟合。

## 你的回合
请根据上述框架和风格，分析提供的图片内容。
```

### 组件 D: Obsidian 写入器 (`file_manager.py`)
**功能:**
- 文件名清洗（去除非法字符）。
- 写入 `00_Master_Index.md`，格式如下：
  `- [[analysis_fig_3|Figure 3 深度解析]]`
- 写入分支笔记 (Child Notes)，包含元数据 (Frontmatter)：
  ```yaml
  ---
  parent: [[00_Master_Index]]
  tags: [paper, analysis, figure]
  ---
  ```

## 5. 给 Codex 的实施路线图

**步骤 1: 环境配置**
安装依赖: `pymupdf`, `openai`, `pydantic`.

**步骤 2: 实现图像处理**
编写 `PDFProcessor` 类，处理 `fitz` 的渲染和 Base64 转换。

**步骤 3: 定义数据结构**
使用 `Pydantic` 定义 `Outline` (大纲) 和 `Section` (板块) 的 Schema，确保 GPT 输出稳定的 JSON。

**步骤 4: 实现核心逻辑 ("智能"部分)**
- 实现 `generate_outline()`: 使用 GPT-4o-mini (纯文本即可)。
- 实现 `analyze_section()`: 使用 GPT-4o (开启视觉能力)。**关键:** 必须注入第 4 节中定义的“思维框架”和“风格样本”提示词。

**步骤 5: 文件生成**
遍历分析结果，将内容写入指定 Vault 路径下的 `.md` 文件。

## 6. 约束与边界情况
- **Token 限制:** 不要将整本 PDF 的文本一次性喂给分析师 Agent。只发送相关的 1-2 页图片 + 具体查询意图。
- **数学公式:** 确保 LaTeX 公式两端包含 `$` 或 `$$`，以便 Obsidian 正确渲染。
- **图片清晰度:** PyMuPDF 的渲染 DPI 至少设为 300，否则 AI 可能看不清公式下标。