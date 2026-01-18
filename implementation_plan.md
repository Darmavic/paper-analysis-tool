# 实施计划 - 结构完整性与可读性优化

## 目标
1.  **结构检验 (Structure Check)**: 确保分析覆盖核心章节（IMRAD），并允许用户配置是否分析附录。
2.  **可读性排版 (Readability)**: 拒绝长篇大论，要求“结构化、列表化、重点加粗”。

## 拟定修改 (analyze_paper.py)

### 1. 结构控制 (Main & Architect)
*   **参数新增**: `parser.add_argument("--include_appendix", action="store_true")`.
*   **Prompt 调整**:
    *   告诉 ArchitectAgent 是否包含 Appendix。
    *   **结构自检**: Architect 返回 Outline 后，代码简单检查是否包含 `Introduction`, `Result` 等关键词（Soft Warn）。

### 2. 排版优化 (AnalystAgent)
*   **Prompt 升级**:
    *   在 System Prompt 中增加 **Visual Readability Rules**:
        *   "段落长度限制：每个段落不超过 5 行。"
        *   "关键词加粗：对核心概念使用 **Bold**。"
        *   "列表化：涉及多个点时，必须使用 Bullet Points。"
        *   "引用块：总结性句子使用 `> Blockquote`。"

### 3. 代码变更点
*   `main()`: 解析 `--include_appendix` 并传给 Architect.
*   `ArchitectAgent`: 接收配置，调整 Prompt。
*   `AnalystAgent`: 调整 System Prompt 中的【格式规范】部分。

## 验证计划
*   **Test**: 运行脚本带 `--include_appendix` 看看是否生成 Appendix 章节。
*   **Check**: 检查生成的 Markdown 文件，确认是否使用了由点列表和加粗，不再是“一坨文字”。
