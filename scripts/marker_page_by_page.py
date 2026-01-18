"""
Marker PDF 逐页处理脚本 (最终版)
针对4GB VRAM优化 - 每次只处理一页，避免内存溢出
"""
import subprocess
import sys
from pathlib import Path
import fitz  # PyMuPDF for page count

def process_pdf_page_by_page(pdf_path: str, output_dir: str = None):
    """
    逐页处理PDF，避免内存问题
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录（可选）
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return
    
    # 获取PDF总页数
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()
    
    print(f"📄 PDF文件: {pdf_path.name}")
    print(f"📊 总页数: {total_pages}")
    print(f"🎯 策略: 逐页处理，避免VRAM不足")
    print("=" * 60)
    
    # 设置输出目录
    if output_dir is None:
        output_dir = Path("marker_output")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # marker_single的可执行文件路径
    marker_exe = Path(sys.executable).parent / "marker_single.exe"
    if not marker_exe.exists():
        marker_exe = Path(sys.executable).parent / "marker_single"
    
    # 逐页处理
    all_markdown = []
    success_count = 0
    fail_count = 0
    
    for page_num in range(total_pages):
        print(f"\n📖 处理第 {page_num + 1}/{total_pages} 页...")
        
        # 调用marker_single处理单页
        try:
            result = subprocess.run(
                [
                    str(marker_exe),
                    str(pdf_path),
                    "--page_range", f"{page_num}-{page_num}",
                    "--output_dir", str(output_dir),
                    "--output_format", "markdown"
                ],
                capture_output=True,
                text=True,
                timeout=180,  # 3分钟超时（单页应该足够）
            )
            
            if result.returncode == 0:
                print(f"✅ 第 {page_num + 1} 页处理成功")
                success_count += 1
            else:
                print(f"❌ 第 {page_num + 1} 页处理失败")
                print(f"错误: {result.stderr[:500]}")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  第 {page_num + 1} 页处理超时（超过3分钟），跳过")
            fail_count += 1
        except Exception as e:
            print(f"❌ 第 {page_num + 1} 页发生错误: {e}")
            fail_count += 1
    
    # Marker会将所有页面的内容合并到一个文件中
    # 检查生成的文件
    generated_md = output_dir / pdf_path.stem / f"{pdf_path.stem}.md"
    
    if generated_md.exists():
        print("\n" + "=" * 60)
        print(f"✅ 处理完成!")
        print(f"📁 输出文件: {generated_md}")
        print(f"📊 成功: {success_count}/{total_pages} 页")
        if fail_count > 0:
            print(f"⚠️  失败: {fail_count} 页")
        
        # 显示文件大小
        file_size = generated_md.stat().st_size
        print(f"📏 文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")
    else:
        print("\n❌ 未找到输出文件，可能处理失败")
        print(f"预期路径: {generated_md}")

if __name__ == "__main__":
    # 测试用
    pdf_path = r"C:\Users\55459\Desktop\研究生组会\组会\25.1.20\Yang and Shadlen - 2007 - Probabilistic reasoning by neurons(1).pdf"
    
    print("🚀 启动Marker逐页处理...")
    print("💡 提示: 每页约20秒，请耐心等待\n")
    
    process_pdf_page_by_page(pdf_path)

