"""
测试去重逻辑
"""
import sys
sys.path.insert(0, r"c:\Users\55459\Desktop\研究生组会\Decision making\lunwen\scripts")

from analyze_paper import SectionIntent, SubQuestion, deduplicate_sections

# 创建测试数据
test_sections = [
    SectionIntent(
        section_title="1. Introduction",
        target_pages=[0],
        filename_slug="intro",
        type="text",
        sub_questions=[SubQuestion(question="测试问题1", question_type="phenomenon")]
    ),
    SectionIntent(
        section_title="Fig. 1a) 任务范式",
        target_pages=[1],
        filename_slug="fig1a",
        type="figure",
        sub_questions=[SubQuestion(question="测试问题2", question_type="phenomenon")]
    ),
    SectionIntent(
        section_title="Fig. 1a 任务设计图解",  # 重复的Fig. 1a
        target_pages=[1],
        filename_slug="fig1a_dup",
        type="figure",
        sub_questions=[SubQuestion(question="测试问题3", question_type="mechanism")]
    ),
    SectionIntent(
        section_title="2. Introduction章节分析",  # 重复的Introduction
        target_pages=[0],
        filename_slug="intro2",
        type="text",
        sub_questions=[SubQuestion(question="测试问题4", question_type="critique")]
    ),
    SectionIntent(
        section_title="Fig. 2 实验结果",  # 不重复
        target_pages=[2],
        filename_slug="fig2",
        type="figure",
        sub_questions=[SubQuestion(question="测试问题5", question_type="phenomenon")]
    ),
]

print("原始sections数量:", len(test_sections))
for i, s in enumerate(test_sections, 1):
    print(f"  {i}. {s.section_title}")

print("\n执行去重...")
unique = deduplicate_sections(test_sections)

print("\n去重后sections数量:", len(unique))
for i, s in enumerate(unique, 1):
    print(f"  {i}. {s.section_title}")

print("\n✅ 预期结果：保留 Introduction(第1个), Fig. 1a(第1个), Fig. 2")
print("✅ 应该移除：Fig. 1a(第2个重复), Introduction(第2个重复)")
