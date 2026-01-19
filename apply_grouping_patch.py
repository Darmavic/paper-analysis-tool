"""
自动应用智能分组功能的补丁脚本

使用方法:
python apply_grouping_patch.py
"""

import re

def apply_patch():
    file_path = r"c:\Users\55459\Desktop\研究生组会\Decision making\lunwen\scripts\analyze_paper.py"
    
    # 读取文件
    print("📖 读取文件...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 修改1: 更新方法签名
    print("🔧 修改1: 更新 generate_outline 方法签名...")
    pattern1 = r'def generate_outline\(self, text_content: str, figures_list: List\[dict\] = None, equations_list: List\[dict\] = None, include_appendix: bool = False\) -> Outline:'
    replacement1 = 'def generate_outline(self, text_content: str, figures_list: List[dict] = None, equations_list: List[dict] = None, visual_groups: dict = None, include_appendix: bool = False) -> Outline:'
    
    content = re.sub(pattern1, replacement1, content)
    
    # 修改2: 更新文档字符串
    print("🔧 修改2: 更新文档字符串...")
    pattern2 = r'(\s+)equations_list: 扫描得到的公式清单.*?\n(\s+)include_appendix: 是否包含附录'
    replacement2 = r'\1equations_list: 扫描得到的公式清单 [{"page": int, "equation_type": str, "description": str}, ...]\n\1visual_groups: 智能分组后的视觉元素 {"figure_groups": [...], "equation_groups": [...]}\n\2include_appendix: 是否包含附录'
    
    content = re.sub(pattern2, replacement2, content)
    
    # 修改3: 替换视觉元素清单构建逻辑
    print("🔧 修改3: 替换视觉元素清单构建逻辑...")
    
    # 找到开始标记
    start_marker = '# 构建视觉元素清单文本（图表+公式）'
    end_marker = 'if visual_elements_text:\n            visual_elements_text += "\\n**强制要求**: 以上所有图表和公式都必须在你的分析大纲中体现！\\n"'
    
    new_logic = '''# 构建视觉元素清单文本（使用分组信息）
        visual_elements_text = ""
        
        if visual_groups:
            # 使用分组后的信息
            figure_groups = visual_groups.get("figure_groups", [])
            equation_groups = visual_groups.get("equation_groups", [])
            
            if figure_groups:
                visual_elements_text = "\\n\\n## 已检测到的图表清单（智能分组）\\n"
                for group in figure_groups:
                    pages_str = ','.join([str(p+1) for p in group['pages']])
                    if group['group_type'] == 'subfigures':
                        visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (子图组，{len(group['items'])}个)\\n"
                    else:
                        visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\\n"
            
            if equation_groups:
                visual_elements_text += "\\n## 已检测到的公式清单（智能分组）\\n"
                numbered_groups = [g for g in equation_groups if any(eq['equation_type'] == 'numbered' for eq in g['items'])]
                unnumbered_groups = [g for g in equation_groups if all(eq['equation_type'] == 'unnumbered' for eq in g['items'])]
                
                if numbered_groups:
                    visual_elements_text += "\\n### 编号公式组\\n"
                    for group in numbered_groups:
                        pages_str = ','.join([str(p+1) for p in set(group['pages'])])
                        if group['group_type'] == 'related':
                            similarity = group.get('similarity_score', 0)
                            visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (关联组，相似度:{similarity:.2f})\\n"
                        else:
                            visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\\n"
                
                if unnumbered_groups:
                    visual_elements_text += "\\n### 未编号公式组\\n"
                    for group in unnumbered_groups:
                        pages_str = ','.join([str(p+1) for p in set(group['pages'])])
                        if group['group_type'] == 'related':
                            similarity = group.get('similarity_score', 0)
                            visual_elements_text += f"- 第{pages_str}页: **{group['group_description']}** (关联组，相似度:{similarity:.2f})\\n"
                        else:
                            visual_elements_text += f"- 第{pages_str}页: {group['group_description']}\\n"
        else:
            # 降级到旧逻辑（未分组）
            if figures_list:
                visual_elements_text = "\\n\\n## 已检测到的图表清单（必须全部分析）\\n"
                for fig in figures_list:
                    visual_elements_text += f"- 第{fig['page']+1}页: {fig['caption']}\\n"
            
            if equations_list:
                visual_elements_text += "\\n## 已检测到的公式清单（必须全部分析）\\n"
                visual_elements_text += "\\n### 编号公式\\n"
                numbered_eqs = [eq for eq in equations_list if eq['equation_type'] == 'numbered']
                if numbered_eqs:
                    for eq in numbered_eqs:
                        visual_elements_text += f"- 第{eq['page']+1}页: {eq['description']}\\n"
                else:
                    visual_elements_text += "- (未检测到编号公式)\\n"
                
                visual_elements_text += "\\n### 重要的未编号公式\\n"
                unnumbered_eqs = [eq for eq in equations_list if eq['equation_type'] == 'unnumbered']
                if unnumbered_eqs:
                    for eq in unnumbered_eqs:
                        visual_elements_text += f"- 第{eq['page']+1}页: {eq['description']}\\n"
                else:
                    visual_elements_text += "- (未检测到重要未编号公式)\\n"
        
        if visual_elements_text:
            visual_elements_text += "\\n**强制要求**: 以上所有图表和公式（及其分组）都必须在你的分析大纲中体现！\\n"
            visual_elements_text += "**分组说明**: \\n"
            visual_elements_text += "- 子图组（如Fig 1a-c）应创建单个section统一分析\\n"
            visual_elements_text += "- 关联公式组应创建单个section，问题需涵盖组内所有公式\\n"
            visual_elements_text += "- 相似度高的公式组说明它们主题相关，应一起分析\\n"'''
    
    # 保留缩进
    indented_new_logic = '        ' + new_logic.replace('\n', '\n        ')
    
    # 使用更精确的模式匹配
    pattern3 = r'# 构建视觉元素清单文本（图表\+公式）.*?if visual_elements_text:\s+visual_elements_text \+= "\\n\*\*强制要求\*\*: 以上所有图表和公式都必须在你的分析大纲中体现！\\n"'
    
    import re
    content =re.sub(pattern3, indented_new_logic, content, flags=re.DOTALL)
    
    # 检查是否有修改
    if content == original_content:
        print("⚠️  警告: 没有应用任何修改。请检查文件格式是否符合预期。")
        print("建议手动按照 GROUPING_INTEGRATION_GUIDE.md 进行修改")
        return False
    
    # 备份原文件
    backup_path = file_path + ".backup"
    print(f"💾 备份原文件到: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    # 写入修改后的内容
    print("✍️  写入修改...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 补丁应用成功！")
    print("\n下一步:")
    print("1. 查看 GROUPING_INTEGRATION_GUIDE.md 中的步骤3和步骤4")
    print("2. 手动在main()函数中添加分组调用")
    print("3. 更新Architect调用传递visual_groups参数")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("智能分组功能自动补丁脚本")
    print("=" * 60)
    print()
    
    success = apply_patch()
    
    if success:
        print("\n🎉 部分修改已自动完成！")
        print("⚠️  仍需手动完成main()函数的修改（见GROUPING_INTEGRATION_GUIDE.md）")
    else:
        print("\n❌ 自动补丁失败，请手动修改")
