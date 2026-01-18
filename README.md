# 学术论文智能分析工具 (Academic Paper Analysis Tool)

基于 Marker OCR + LLM 的学术论文深度分析工具，支持公式识别和 Obsidian 笔记自动生成。

## ✨ 核心功能

- 📄 **高精度PDF识别**：使用 Marker 进行逐页OCR，完美识别LaTeX公式
- 🧠 **智能大纲生成**：AI Architect 自动提取论文核心问题
- 🔍 **深度分析**：AI Analyst 对每个问题进行多维度解析
- 📝 **Obsidian笔记**：自动生成结构化笔记，支持双向链接
- 🔄 **批量去重**：智能识别重复内容，避免冗余分析

## 🚀 快速开始

### 本地部署

```bash
# 1. 克隆仓库
git clone https://github.com/Darmavic/paper-analysis-tool.git
cd paper-analysis-tool

# 2. 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. 安装依赖
pip install -r scripts/requirements.txt

# 4. 配置API密钥
echo "OPENROUTER_API_KEY=your_api_key_here" > .env

# 5. 运行分析
python scripts/analyze_paper.py --pdf your_paper.pdf --vault output_folder
```

### AutoDL/云服务器部署

```bash
# 1. 克隆仓库
git clone https://github.com/Darmavic/paper-analysis-tool.git
cd paper-analysis-tool

# 2. 运行一键部署脚本
bash deploy.sh

# 3. 上传PDF并运行分析
python scripts/analyze_paper.py --pdf /path/to/paper.pdf --vault /path/to/output
```

## ⚙️ 配置说明

### 环境变量 (`.env`)

```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```

### VRAM优化

脚本会自动检测GPU并优化VRAM设置：
- **本地（4GB VRAM）**：已优化为低显存模式
- **AutoDL（24GB VRAM）**：可手动调整 `analyze_paper.py` 中的：
  ```python
  os.environ["INFERENCE_RAM"] = "24"
  os.environ["VRAM_PER_TASK"] = "20"
  ```

## 📊 处理时间参考

| 环境 | GPU | 单页耗时 | 8页论文总耗时 |
|------|-----|---------|--------------|
| 本地 | 4GB VRAM | ~2-3分钟 | ~45-60分钟 |
| AutoDL | 24GB VRAM | ~20-30秒 | ~10-15分钟 |

## 📁 项目结构

```
paper-analysis-tool/
├── scripts/
│   ├── analyze_paper.py      # 主分析脚本
│   ├── requirements.txt       # Python依赖
│   └── test_*.py             # 测试脚本
├── .env.example              # 环境变量模板
├── .gitignore
├── deploy.sh                 # 自动部署脚本
└── README.md
```

## 🛠️ 依赖项

- Python 3.9+
- marker-pdf (OCR引擎)
- openai (LLM API)
- pymupdf (PDF处理)
- pydantic (数据验证)

## 📝 使用示例

```bash
# 基本用法
python scripts/analyze_paper.py \
    --pdf paper.pdf \
    --vault ./obsidian_vault

# 包含附录分析
python scripts/analyze_paper.py \
    --pdf paper.pdf \
    --vault ./obsidian_vault \
    --include-appendix
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## ⚠️ 注意事项

1. **API密钥安全**：请勿将 `.env` 文件上传到 GitHub
2. **显存要求**：Marker 至少需要 4GB VRAM，推荐 8GB+
3. **网络连接**：需要稳定的网络连接以访问 OpenRouter API
