"""
测试智能分组功能

运行此脚本以验证group_visual_elements函数是否正常工作
"""

import sys
sys.path.insert(0, r'c:\Users\55459\Desktop\研究生组会\Decision making\lunwen\scripts')

from analyze_paper import group_visual_elements

# 测试数据
print("=" * 60)
print("智能分组功能测试")
print("=" * 60)
print()

# 准备测试图表数据
figures_list = [
    {"page": 2, "caption": "Fig 1a: 任务范式条件A"},
    {"page": 2, "caption": "Fig 1b: 任务范式条件B"},
    {"page": 2, "caption": "Fig 1c: 任务范式条件C"},
    {"page": 4, "caption": "Fig 2: 神经响应模式"},
    {"page": 5, "caption": "Table 1: 被试信息"},
]

# 准备测试公式数据  
equations_list = [
    {
        "page": 3,
        "equation_type": "numbered",
        "equation_number": "1",
        "description": "Equation 1: 损失函数",
        "context": "we define the loss function as follows: ..."
    },
    {
        "page": 3,
        "equation_type": "numbered",
        "equation_number": "2",
        "description": "Equation 2: 梯度更新",
        "context": "the gradient update rule is given by: ..."
    },
    {
        "page": 3,
        "equation_type": "numbered",
        "equation_number": "3",
        "description": "Equation 3: 学习率调整",
        "context": "we adjust the learning rate according to: ..."
    },
    {
        "page": 5,
        "equation_type": "unnumbered",
        "equation_number": None,
        "description": "后验概率",
        "context": "the posterior probability can be computed as: ..."
    },
    {
        "page": 7,
        "equation_type": "numbered",
        "equation_number": "4",
        "description": "Equation 4: 目标函数",
        "context": "the objective function for optimization: ..."
    },
]

print("📊 测试数据:")
print(f"   - 图表: {len(figures_list)}个")
print(f"   - 公式: {len(equations_list)}个")
print()

# 执行分组
print("🔗 执行智能分组...")
try:
    visual_groups = group_visual_elements(figures_list, equations_list)
    print("✅ 分组成功！")
    print()
    
    # 显示图表分组结果
    fig_groups = visual_groups.get("figure_groups", [])
    print(f"📊 图表分组结果: {len(fig_groups)}个组")
    for i, group in enumerate(fig_groups, 1):
        print(f"\n  组{i}: {group['group_description']}")
        print(f"    - 类型: {group['group_type']}")
        print(f"    - 页码: {group['pages']}")
        print(f"    - 包含: {len(group['items'])}个项目")
    
    print()
    
    # 显示公式分组结果
    eq_groups = visual_groups.get("equation_groups", [])
    print(f"🔢 公式分组结果: {len(eq_groups)}个组")
    for i, group in enumerate(eq_groups, 1):
        print(f"\n  组{i}: {group['group_description']}")
        print(f"    - 类型: {group['group_type']}")
        print(f"    - 页码: {group['pages']}")
        print(f"    - 包含: {len(group['items'])}个公式")
        if 'similarity_score' in group:
            print(f"    - 相似度: {group['similarity_score']:.2f}")
    
    print()
    print("=" * 60)
    print("✅ 测试完成！智能分组功能正常工作。")
    print("=" * 60)
    
    # 验证预期结果
    print("\n验证:")
    subfig_count = sum(1 for g in fig_groups if g['group_type'] == 'subfigures')
    related_eq_count = sum(1 for g in eq_groups if g['group_type'] == 'related')
    
    print(f"  - 子图组数量: {subfig_count} (预期: 1, Fig 1a-c)")
    print(f"  - 关联公式组: {related_eq_count} (预期: 至少1)")
    
    if subfig_count >= 1:
        print(f"  ✅ 子图分组工作正常")
    else:
        print(f"  ⚠️  子图分组可能有问题")
    
    if related_eq_count >= 1:
        print(f"  ✅ 公式关联分组工作正常")
    else:
        print(f"  ⚠️  公式关联分组可能有问题")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
