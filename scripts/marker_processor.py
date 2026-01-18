"""
Marker集成到论文分析工具 - 使用Marker替代PyMuPDF以获得公式识别能力
"""
import subprocess
import sys
from pathlib import Path

class MarkerProcessor:
    """使用Marker处理PDF，支持公式识别和LaTeX转换"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.marker_exe = Path(sys.executable).parent / "marker_single.exe"
        if not self.marker_exe.exists():
            self.marker_exe = Path(sys.executable).parent / "marker_single"
        
        # 设置输出目录
        self.output_dir = Path("marker_temp_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 获取PDF总页数（仍需PyMuPDF）
        import fitz
        doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(doc)
        doc.close()
    
    def get_text(self, start_page: int = 0, num_pages: int = 3) -> str:
        """
        提取前几页文本用于生成大纲
        使用Marker逐页处理，然后合并
        """
        print(f"📊 使用Marker提取前{num_pages}页文本...")
        
        all_text = []
        for i in range(min(num_pages, self.total_pages)):
            page_num = start_page + i
            print(f"  处理第{page_num + 1}页...")
            
            try:
                result = subprocess.run(
                    [
                        str(self.marker_exe),
                        str(self.pdf_path),
                        "--page_range", f"{page_num}-{page_num}",
                        "--output_dir", str(self.output_dir),
                        "--output_format", "markdown"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120  # 2分钟超时
                )
                
                if result.returncode == 0:
                    # 读取生成的markdown
                    md_file = self.output_dir / self.pdf_path.stem / f"{self.pdf_path.stem}.md"
                    if md_file.exists():
                        with open(md_file, "r", encoding="utf-8") as f:
                            text = f.read()
                        all_text.append(text)
                else:
                    print(f"  ⚠️ 第{page_num + 1}页处理失败，使用PyMuPDF备用方案")
                    # 降级到PyMuPDF
                    import fitz
                    doc = fitz.open(str(self.pdf_path))
                    all_text.append(doc[page_num].get_text())
                    doc.close()
                    
            except Exception as e:
                print(f"  ⚠️ Marker出错: {e}，使用PyMuPDF备用方案")
                import fitz
                doc = fitz.open(str(self.pdf_path))
                all_text.append(doc[page_num].get_text())
                doc.close()
        
        return "\n\n".join(all_text)
    
    def get_page_image(self, page_number: int, dpi: int = 300) -> str:
        """
        获取页面图片（用于Analyst分析）
        仍使用PyMuPDF，因为Marker不提供图片渲染
        """
        import fitz
        import base64
        
        if not (0 <= page_number < self.total_pages):
            raise ValueError(f"Page {page_number} out of range")
        
        doc = fitz.open(str(self.pdf_path))
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes("png")
        doc.close()
        
        return base64.b64encode(img_data).decode("utf-8")
    
    def close(self):
        """清理临时文件"""
        import shutil
        if self.output_dir.exists():
            try:
                shutil.rmtree(self.output_dir)
            except:
                pass

# 使用示例：将analyze_paper.py中的PDFProcessor替换为MarkerProcessor即可
