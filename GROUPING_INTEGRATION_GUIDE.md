# 智能分组功能集成指南

## 已完成的工作

✅ 已添加 `group_visual_elements()` 函数 (analyze_paper.py Line 687)
- 图表子图自动分组 (Fig 1a, 1b, 1c)
- 公式关联度智能分组 (1-4个为一组)

## 待完成：集成到主流程

### 步骤1: 更新Architect.generate_outline方法签名

**位置**: Line 1343

**修改前**:
```python
def generate_outline(self, text_content: str, figures_list: List[dict] = None, equations_list: List[dict] = None, include_appendix: bool = False) -> Outline:
```

**修改后**:
```python  
def generate_outline(self, text_content: str, figures_list: List[dict] = None, equations_list: List[dict] = None, visual_groups: dict = None, include_appendix: bool = False) -> Outline:
```

### 步骤2: 更新视觉元素清单构建逻辑

**位置**: Line 1354-1381  
**文件**: analyze_paper.py

**替换内容：从 Line 1354 的 `# 构建视觉元素清单文本` 到 Line 1381 的 `visual_elements_text += ...`**

**新代码**:
```python
        # 构建视觉元素清单文本（使用分组信息）
        visual_elements_text = ""
        
        if visual_groups:
            # 使用分组后的信息
            figure_groups = visual_groups.get("figure_groups", [])
            equation_groups = visual_groups.get("equation_groups", [])
            
            if figure_groups:
                visual_elements_text = "\n\n## 已检测到的图表清单（智能分组）\n"
                for group in figure_groups:
                    pages_str = ','.join([str(p+1) for p in group['pages']])
                    if group['group_type'] == 'subfigures':
                        visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (子图组，{len(group['items'])}个)\n"
                    else:
                        visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\n"
            
            if equation_groups:
                visual_elements_text += "\n## 已检测到的公式清单（智能分组）\n"
                numbered_groups = [g for g in equation_groups if any(eq['equation_type'] == 'numbered' for eq in g['items'])]
                unnumbered_groups = [g for g in equation_groups if all(eq['equation_type'] == 'unnumbered' for eq in g['items'])]
                
                if numbered_groups:
                    visual_elements_text += "\n### 编号公式组\n"
                    for group in numbered_groups:
                        pages_str = ','.join([str(p+1) for p in set(group['pages'])])
                        if group['group_type'] == 'related':
                            similarity = group.get('similarity_score', 0)
                            visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (关联组，相似度:{similarity:.2f})\n"
                        else:
                            visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\n"
                
                if unnumbered_groups:
                    visual_elements_text += "\n### 未编号公式组\n"
                    for group in unnumbered_groups:
                        pages_str = ','.join([str(p+1) for p in set(group['pages'])])
                        if group['group_type'] == 'related':
                            similarity = group.get('similarity_score', 0)
                            visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (关联组，相似度:{similarity:.2f})\n"
                        else:
                            visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\n"
        else:
            # 降级到旧逻辑（未分组）
            if figures_list:
                visual_elements_text = "\n\n## 已检测到的图表清单（必须全部分析）\n"
                for fig in figures_list:
                    visual_elements_text += f"- 第{fig['page']+1}页: {fig['caption']}\n"
            
            if equations_list:
                visual_elements_text += "\n## 已检测到的公式清单（必须全部分析）\n"
                visual_elements_text += "\n### 编号公式\n"
                numbered_eqs = [eq for eq in equations_list if eq['equation_type'] == 'numbered']
                if numbered_eqs:
                    for eq in numbered_eqs:
                        visual_elements_text += f"- 第{eq['page']+1}页: {eq['description']}\n"
                else:
                    visual_elements_text += "- (未检测到编号公式)\n"
                
                visual_elements_text += "\n### 重要的未编号公式\n"
                unnumbered_eqs = [eq for eq in equations_list if eq['equation_type'] == 'unnumbered']
                if unnumbered_eqs:
                    for eq in unnumbered_eqs:
                        visual_elements_text += f"- 第{eq['page']+1}页: {eq['description']}\n"
                else:
                    visual_elements_text += "- (未检测到重要未编号公式)\n"
        
        if visual_elements_text:
            visual_elements_text += "\n**强制要求**: 以上所有图表和公式（及其分组）都必须在你的分析大纲中体现！\n"
            visual_elements_text += "**分组说明**: \n"
            visual_elements_text += "- 子图组（如Fig 1a-c）应创建单个section统一分析\n"
            visual_elements_text += "- 关联公式组应创建单个section，问题需涵盖组内所有公式\n"
            visual_elements_text += "- 相似度高的公式组说明它们主题相关，应一起分析\n"
```

### 步骤3: 更新main()函数，添加分组步骤

**位置**: 在公式扫描之后 (约Line 1918附近)

**添加以下代码**:
```python
    # NEW: 智能分组视觉元素
    print("🔗 智能分组: 正在对图表和公式进行智能分组...")
    visual_groups = group_visual_elements(figures_list, equations_list)
    
    # 打印分组统计
    if visual_groups:
        fig_groups = visual_groups.get("figure_groups", [])
        eq_groups = visual_groups.get("equation_groups", [])
        
        if fig_groups:
            subfig_count = sum(1 for g in fig_groups if g['group_type'] == 'subfigures')
            print(f"   - 图表分组: {len(fig_groups)}个组")
            if subfig_count > 0:
                print(f"     * 子图组: {subfig_count}个")
        
        if eq_groups:
            related_count = sum(1 for g in eq_groups if g['group_type'] == 'related')
            total_eqs_in_groups = sum(len(g['items']) for g in eq_groups if g['group_type'] == 'related')
            print(f"   - 公式分组: {len(eq_groups)}个组")
            if related_count > 0:
                avg_group_size = total_eqs_in_groups / related_count if related_count > 0 else 0
                print(f"     * 关联组: {related_count}个 (平均每组{avg_group_size:.1f}个公式)")
```

### 步骤4: 更新Architect调用，传递visual_groups

**位置**: 约Line 1940附近的 `architect.generate_outline` 调用

**修改前**:
```python
            batch_outline = architect.generate_outline(
                batch_text, 
                figures_list=figures_list if batch_idx == 0 else None,
                equations_list=equations_list if batch_idx == 0 else None,
                include_appendix=args.include_appendix
            )
```

**修改后**:
```python
            batch_outline = architect.generate_outline(
                batch_text, 
                figures_list=figures_list if batch_idx == 0 else None,
                equations_list=equations_list if batch_idx == 0 else None,
                visual_groups=visual_groups if batch_idx == 0 else None,  # 新增
                include_appendix=args.include_appendix
            )
```

---

## 预期效果

运行后，控制台将显示：

```
📊 图表扫描: 正在识别PDF中的所有图表...
✅ 检测到 15 个图表/表格

🔢 公式扫描: 正在识别Marker输出中的所有公式...
✅ 检测到 18 个公式
   - 编号公式: 8
   - 重要未编号公式: 10

🔗 智能分组: 正在对图表和公式进行智能分组...
   - 图表分组: 12个组
     * 子图组: 3个
   - 公式分组: 10个组
     * 关联组: 4个 (平均每组2.5个公式)

架构师: 正在分批生成深度阅读大纲...
```

Architect的prompt中将包含：

```
## 已检测到的图表清单（智能分组）
- 第3,4页: **Fig 1a-c** (子图组，3个)
- 第5页: Fig 2: 神经响应模式
- 第7,8页: **Fig 3a-b** (子图组，2个)

## 已检测到的公式清单（智能分组）

### 编号公式组
- 第4,5页: **Equation 1-3: logLR计算步骤** (关联组，相似度:0.85)
- 第6页: Equation 4: 贝叶斯更新

### 未编号公式组
- 第4页: **损失函数定义等相关公式 (2个)** (关联组，相似度:0.72)

**强制要求**: 以上所有图表和公式（及其分组）都必须在你的分析大纲中体现！
**分组说明**: 
- 子图组（如Fig 1a-c）应创建单个section统一分析
- 关联公式组应创建单个section，问题需涵盖组内所有公式
- 相似度高的公式组说明它们主题相关，应一起分析
```

---

## 智能分组算法

### 图表分组
1. 提取基础编号和子编号 (Fig 1a, 1b → base=1, sub=a/b)
2. 按基础编号分组
3. 如果同一基础编号下有多个子图，合并为一组

### 公式分组
1. **关联度计算** (0-1分):
   - 页码接近: 同页+0.2, 相邻页+0.1
   - 上下文相似: 最高+0.4
   - 描述相似: 最高+0.2
   - 连续编号: +0.2

2. **贪心分组**:
   - 每次从剩余公式中选一个作为种子
   - 查找与当前组平均相似度>0.4的公式加入
   - 最多4个为一组
   - 如果没有足够相似的，保持单独

---

## 手动修改说明

由于文件较大，请手动进行以下修改：

1. 打开 `analyze_paper.py`
2. 按照上述步骤1-4逐步修改
3. 保存后运行测试

或者，我可以创建一个完整的补丁脚本为您自动应用这些更改。
