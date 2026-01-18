import fitz
import sys

# 从原始PDF提取第1页
input_pdf = r"C:\Users\55459\Desktop\研究生组会\Decision making\lunwen\pdf\2026.1.20\Yang and Shadlen - 2007 - Probabilistic reasoning by neurons(1).pdf"
output_pdf = r"C:\Users\55459\Desktop\研究生组会\Decision making\lunwen\pdf\2026.1.20\test_first_page.pdf"

doc = fitz.open(input_pdf)
new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=0, to_page=0)
new_doc.save(output_pdf)
new_doc.close()
doc.close()

print(f"✅ 已提取第1页到: {output_pdf}")
