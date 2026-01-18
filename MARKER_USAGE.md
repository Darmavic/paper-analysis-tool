# Marker集成使用指南

## 🎯 功能说明

Marker已成功集成到`analyze_paper.py`，提供**公式识别**和**LaTeX转换**功能。

---

## 🚀 使用方法

### 方法1: 直接修改配置文件

编辑 `scripts/analyze_paper.py`，找到第40行左右：

```python
# PDF处理配置
USE_MARKER = False  # 改为 True 启用Marker
```

### 方法2: 命令行参数（TODO:未实现）

未来可以添加 `--use-marker` 参数

---

## ⚖️ Marker vs PyMuPDF 对比

| 特性 | PyMuPDF (默认) | Marker |
|------|---------------|--------|
| **速度** | ⚡ 极快 (瞬间) | 🐌 较慢 (20秒/页) |
| **公式识别** | ❌ 无 | ✅ LaTeX格式 |
| **表格提取** | ⚠️ 一般 | ✅ 优秀 |
| **文本PDF** | ✅ 完美 | ✅ 完美 |
| **扫描PDF** | ❌ 不支持 | ✅ 内置OCR |
| **VRAM需求** | 0GB | 3-4GB (自动降级) |
| **适合场景** | 快速批量分析 | 公式密集型论文 |

---

## 📊 预计处理时间

**PyMuPDF模式** (USE_MARKER=False):
- Architect阶段: 提取前3页文本 → **< 1秒**
- Analyst阶段: 分析每个图表 → **依赖LLM速度**
- **总时间**: 主要取决于LLM调用，PDF处理几乎不耗时

**Marker模式** (USE_MARKER=True):
- Architect阶段: 提取前3页文本 → **约60秒** (3页×20秒)
- Analyst阶段: 分析每个图表 → **依赖LLM速度** (与PyMuPDF相同)
- **总时间**: PDF处理增加约1分钟，但获得公式识别能力  

---

## 💡 使用建议

### 推荐使用Marker的情况：
- ✅ 论文包含**大量数学公式**
- ✅ 需要提取**LaTeX格式**的公式
- ✅ 处理**扫描版PDF**
- ✅ 您有**充足时间**等待处理

### 推荐使用PyMuPDF的情况：
- ✅ **快速批量**分析多篇论文
- ✅ 论文主要是**文字描述**，公式较少
- ✅ 对处理**速度敏感**
- ✅ **GPU显存不足**（<4GB）

---

## 🛡️ 自动降级机制  

Marker内置了**智能降级**功能：
- 如果Marker处理失败或超时，**自动切换到PyMuPDF**
- 确保程序不会因Marker问题而中断
- 混合模式：部分页面用Marker，失败页面用PyMuPDF

---

## 🧪 测试示例

```python
# 在 scripts/analyze_paper.py 中修改配置
USE_MARKER = True  # 启用Marker

# 然后正常运行
python scripts/analyze_paper.py \
    --pdf "path/to/paper.pdf" \
    --vault "path/to/obsidian/vault"
```

**预期输出**:
```
🔬 使用Marker处理器（支持公式识别）
⏳ Marker处理前3页（约60秒）...
  📖 处理第1页... ✅
  📖 处理第2页... ✅
  📖 处理第3页... ✅
...
```

---

## ⚙️ 技术细节

**MarkerProcessor类特点**:
1. **逐页处理**: 避免4GB VRAM限制
2. **自动降级**: Marker失败时使用PyMuPDF
3. **临时文件清理**: 自动删除中间文件
4. **进度显示**: 实时显示处理进度

**文件位置**:
- 主程序: `scripts/analyze_paper.py`
- Marker处理器: 集成在主程序中 (line 140-226)
- 独立测试: `scripts/marker_page_by_page.py`

---

## 🎓 总结

Marker已成功集成！您现在可以：
- ✅ 快速模式（PyMuPDF）- 日常使用
- ✅ 精确模式（Marker）- 公式密集型论文

只需修改一行配置即可切换！
