# GitHub 上传指南

本文档提供将项目上传到GitHub的详细步骤。

## 📋 准备工作

### 1. 确保已安装Git
```bash
git --version
```

如果未安装，请访问：https://git-scm.com/downloads

### 2. 配置Git（首次使用）
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🚀 上传步骤

### 步骤1：在GitHub上创建新仓库

1. 访问 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - Repository name: `paper-analysis-tool` (或您喜欢的名字)
   - Description: `AI-powered academic paper analysis tool with Marker OCR and LLM`
   - 选择 "Public" 或 "Private"
   - **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

### 步骤2：在本地初始化Git仓库

打开PowerShell，导航到项目目录：

```powershell
cd "c:\Users\55459\Desktop\研究生组会\Decision making\lunwen"

# 初始化Git仓库
git init

# 添加所有文件（.gitignore会自动排除不需要的文件）
git add .

# 创建第一次提交
git commit -m "Initial commit: Academic paper analysis tool"
```

### 步骤3：连接远程仓库并推送

**替换下面的 `YOUR_USERNAME` 为您的GitHub用户名**

```powershell
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/paper-analysis-tool.git

# 推送代码
git push -u origin master
```

如果提示需要认证：
- 使用GitHub的 Personal Access Token (PAT) 而不是密码
- 生成PAT: Settings → Developer settings → Personal access tokens → Generate new token

## ✅ 验证上传

访问您的仓库页面：
```
https://github.com/YOUR_USERNAME/paper-analysis-tool
```

应该能看到所有文件（除了.gitignore中排除的那些）。

## 📝 后续更新

当您修改代码后，使用以下命令同步到GitHub：

```powershell
# 查看修改
git status

# 添加修改的文件
git add .

# 提交修改
git commit -m "描述您的修改"

# 推送到GitHub
git push
```

## 🔧 AutoDL部署

上传到GitHub后，在AutoDL服务器上：

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/paper-analysis-tool.git
cd paper-analysis-tool

# 运行部署脚本
bash deploy.sh

# 配置API密钥
nano .env  # 编辑并填入OPENROUTER_API_KEY

# 开始分析
python scripts/analyze_paper.py --pdf your_paper.pdf --vault output
```

## ⚠️ 安全提示

**绝对不要上传以下文件到GitHub：**
- `.env` (包含API密钥)
- PDF文件 (可能有版权问题)
- `obsidian_vault/` (个人笔记)

这些文件已在 `.gitignore` 中排除，但请务必检查！

## 🆘 常见问题

### Q: 如何检查哪些文件会被上传？
```bash
git status  # 查看待提交的文件
```

### Q: 如何撤销未提交的修改？
```bash
git checkout -- filename  # 撤销单个文件
git reset --hard  # 撤销所有修改（危险！）
```

### Q: 如何更新README中的用户名？
使用文本编辑器打开 `README.md`，将所有 `YOUR_USERNAME` 替换为您的GitHub用户名。
