"""
Marker PDF 测试脚本 - 针对4GB VRAM优化
"""
import os
from pathlib import Path

def test_marker_conversion():
    """测试Marker转换功能"""
    
    # 设置环境变量以优化内存使用
    os.environ["INFERENCE_RAM"] = "4"  # 设置为4GB VRAM
    os.environ["VRAM_PER_TASK"] = "3"  # 每个任务使用3GB
    
    from marker.convert import convert_single_pdf
    from marker.models import load_all_models
    
    # PDF路径
    pdf_path = r"C:\Users\55459\Desktop\研究生组会\组会\25.1.20\Yang and Shadlen - 2007 - Probabilistic reasoning by neurons(1).pdf"
    
    # 输出目录
    output_dir = Path(r"C:\Users\55459\Desktop\研究生组会\Decision making\lunwen\marker_output")
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 开始测试Marker PDF转换...")
    print(f"📄 输入: {pdf_path}")
    print(f"📁 输出: {output_dir}")
    print(f"🎮 GPU配置: 4GB VRAM, 每任务3GB")
    print("-" * 60)
    
    try:
        # 加载模型 (这里可能会占用VRAM)
        print("⏳ 正在加载模型...")
        model_lst = load_all_models()
        
        # 转换PDF
        print("⏳ 正在转换PDF (这可能需要几分钟)...")
        full_text, images, out_meta = convert_single_pdf(
            pdf_path,
            model_lst,
            max_pages=5,  # 先只测试前5页，避免内存溢出
            langs=["zh", "en"]
        )
        
        # 保存结果
        output_file = output_dir / "converted.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print("✅ 转换成功!")
        print(f"📝 Markdown已保存到: {output_file}")
        print(f"📊 提取了 {len(images)} 张图片")
        print(f"📏 文本长度: {len(full_text)} 字符")
        
        # 显示前500字符预览
        print("\n" + "="*60)
        print("📖 内容预览 (前500字符):")
        print("="*60)
        print(full_text[:500])
        print("...")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        print("\n可能的原因:")
        print("1. VRAM不足 (4GB可能不够) - 尝试减少max_pages")
        print("2. 某些依赖缺失 - 检查错误信息")
        print("3. CUDA版本不匹配 - 确认PyTorch和CUDA兼容")
        raise

if __name__ == "__main__":
    test_marker_conversion()
