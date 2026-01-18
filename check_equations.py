import fitz  # PyMuPDF
import re

pdf_path = r"C:\Users\55459\Desktop\研究生组会\Decision making\lunwen\pdf\2026.1.20\41_RNNs_reveal_a_new_optimal_s.pdf"

doc = fitz.open(pdf_path)

# 更精确的公式编号模式
equation_patterns = [
    (r'Equation\s+(\d+)', 'Equation'),
    (r'Eq\.\s*(\d+)', 'Eq.'),
    (r'equation\s+\((\d+)\)', 'equation'),
]

# 排除参考文献年份的模式
def is_likely_year(num_str):
    """判断是否可能是年份"""
    num = int(num_str)
    return 1900 <= num <= 2100

found_equations = {}

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    
    for pattern, label in equation_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            eq_num = match.group(1)
            if not is_likely_year(eq_num):  # 排除年份
                key = f"{label} {eq_num}"
                if key not in found_equations:
                    found_equations[key] = page_num + 1

# 也检查独立的编号（在上下文中可能是公式）
standalone_pattern = r'\n\s*\((\d+)\)\s*\n'
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    matches = re.finditer(standalone_pattern, text)
    for match in matches:
        eq_num = match.group(1)
        if not is_likely_year(eq_num) and int(eq_num) < 50:  # 小于50的独立编号
            key = f"({eq_num})"
            if key not in found_equations:
                found_equations[key] = page_num + 1

doc.close()

print("找到的可能公式编号：")
if found_equations:
    for eq, page in sorted(found_equations.items(), key=lambda x: (x[1], x[0])):
        print(f"  Page {page}: {eq}")
    print(f"\n总计: {len(found_equations)} 个可能的公式编号")
    print("\n✅ 这篇论文可能有编号公式")
    print("建议：添加EquationScanner扫描Marker转换的LaTeX公式")
else:
    print("  未找到明确的公式编号")
    print("\n⚠️  可能原因：")
    print("  1. 论文使用内嵌公式（没有编号）")
    print("  2. 公式编号格式特殊")
    print("建议：检查Marker输出的LaTeX")
