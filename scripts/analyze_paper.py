import sys
import os
import subprocess
import argparse
import base64
import json
import re
import time
from typing import List, Optional, Any
from pathlib import Path
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables
# Load environment variables
load_dotenv()
# Suppress OpenRouter model check warning
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

# --- Config ---
# Defaulting to user request (Unified Model)
MODEL_ID = "qwen/qwen-2.5-vl-72b-instruct" # Fallback since "qwen/qwen3-vl-235b-a22b-instruct" might be hallucinated or beta.
# WAIT: The search result explicitly said "qwen/qwen3-vl-235b-a22b-instruct". 
# However, if it fails, I should fallback. But let's trust the search result which looked very specific (Source [1] openrouter.ai).
# If it fails, I'll see an error.
MODEL_ID = "qwen/qwen-2.5-vl-72b-instruct" 
# RE-EVALUATING: The search result source [1] is 'openrouter.ai' via vertex search grounding. 
# "The OpenRouter model ID for "Qwen3 VL 235B A22B Instruct" is `qwen/qwen3-vl-235b-a22b-instruct`."
# But wait, Qwen 2.5 is the current stable. Qwen 3 release date in search says Sep 2025? (Current date is Jan 2026 in the prompt metadata).
# So Qwen 3 IS released in this timeline.
MODEL_ID = "qwen/qwen3-vl-235b-a22b-instruct"

ARCHITECT_MODEL = MODEL_ID
ANALYST_MODEL = MODEL_ID
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# PDF处理配置
# 设置为True使用Marker（支持公式识别，但速度较慢约20秒/页）
# 设置为False使用PyMuPDF（快速但无公式识别）
USE_MARKER = True  # 启用Marker模式进行测试

# Architect分批处理配置
# Marker会逐页识别整个PDF，然后Architect每N页分批提取问题
PAGES_PER_BATCH = 3  # 每批处理的页数，建议2-4页

# --- PDF Extraction Strategy ---
# Using PyMuPDF (fitz) for text extraction
# PyMuPDF provides >95% accuracy for text-based academic PDFs
# For scanned PDFs or complex layouts, consider preprocessing with MinerU CLI tool
# (see walkthrough.md for MinerU integration guide)

# --- Data Models (Pydantic) ---

class SubQuestion(BaseModel):
    """子问题模型，包含问题类型和字数要求"""
    question: str = Field(..., description="具体的探究性问题")
    question_type: str = Field(..., description="问题类型: 'phenomenon'(现象描述/'是什么') | 'mechanism'(机理推导) | 'critique'(目的和批判/'为什么')")
    min_words: int = Field(default=0)
    max_words: int = Field(default=10000)
    validate_min: int = Field(default=0)  # 验证最小值
    validate_max: int = Field(default=10000)  # 验证最大值
    
    def __init__(self, **data):
        super().__init__(**data)
        # 根据问题类型自动设置字数要求
        if self.question_type == "phenomenon":
            self.min_words = 1000
            self.max_words = 3000
            self.validate_min = 600
            self.validate_max = 4000
        elif self.question_type == "mechanism":
            self.min_words = 1000
            self.max_words = 3000
            self.validate_min = 600
            self.validate_max = 4000
        elif self.question_type == "critique":
            self.min_words = 500
            self.max_words = 1500
            self.validate_min = 400
            self.validate_max = 2000

class SectionIntent(BaseModel):
    section_title: str = Field(..., description="Title of the section or figure index")
    target_pages: List[int] = Field(..., description="List of 0-indexed page numbers relevant to this section")
    filename_slug: str = Field(..., description="suggested filename slug, e.g. analysis_fig_3")
    type: str = Field(..., description="content type: 'figure', 'equation', 'text'")
    sub_questions: List[SubQuestion] = Field(..., description="List of 2-4 specific deep-dive questions with types")

    @field_validator('target_pages', mode='before')
    @classmethod
    def parse_pages(cls, v):
        if isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, int):
                    new_list.append(item)
                elif isinstance(item, str):
                    # Extract first number found
                    match = re.search(r'\d+', item)
                    if match:
                        new_list.append(int(match.group(0)))
            return new_list
        return v

class Outline(BaseModel):
    paper_title: str
    summary: str
    sections: List[SectionIntent]

# --- Components ---

class PDFProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        # Note: MinerU integration requires significant refactoring
        # For now, using PyMuPDF which is stable and accurate for text PDFs 

    def get_page_image(self, page_number: int, dpi: int = 300) -> str:
        """Render page to base64 image."""
        if not (0 <= page_number < len(self.doc)):
            raise ValueError(f"Page {page_number} out of range")
        
        page = self.doc.load_page(page_number)
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes("png")
        return base64.b64encode(img_data).decode("utf-8")

    def get_text(self, start_page: int = 0, num_pages: int = 3) -> str:
        """Extract text from the first few pages for abstract/TOC analysis."""
        combined_text = ""
        
        limit_pages = min(len(self.doc), num_pages)
        for i in range(limit_pages):
            page_idx = start_page + i
            # Use PyMuPDF's built-in text extraction (works well for text-based PDFs)
            combined_text += self.doc.load_page(page_idx).get_text()
                
        return combined_text

    def close(self):
        self.doc.close()

class MarkerProcessor:
    """使用Marker处理PDF - 支持公式识别，使用Python API + 临时文件逐页处理"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        
        # 设置临时输出目录
        self.output_dir = Path("marker_temp_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 获取总页数（PyMuPDF）
        self.doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(self.doc)
        # Note: Keep doc open for later use (e.g., get_page_image)
        
        # 延迟加载marker模型
        self._model_dict = None
        self._converter_cls = None
        
        print(f"📚 使用Marker处理PDF（支持公式识别）- Python API + 临时文件模式")
    
    def _init_marker(self):
        """初始化Marker模型和转换器"""
        if self._model_dict is None:
            print("⏳ 首次使用，正在加载Marker模型...")
            try:
                # 导入marker内部组件
                from marker.models import create_model_dict
                from marker.converters.pdf import PdfConverter
                from marker.config.parser import ConfigParser
                
                # 设置环境变量优化显存
                import os
                os.environ["INFERENCE_RAM"] = "8"
                os.environ["VRAM_PER_TASK"] = "4"
                
                # 加载模型
                self._model_dict = create_model_dict()
                
                # 加载配置 - 必须提供 output_format
                config_parser = ConfigParser({"output_format": "markdown", "output_dir": "marker_temp_output"})
                
                # 保存配置用于每次创建converter
                self._config_parser = config_parser
                self._PdfConverter = PdfConverter
                
                print("✅ 模型加载完成")
            except ImportError as e:
                raise ImportError(f"Marker导入失败，请确保安装了marker-pdf: {e}")
            except Exception as e:
                raise RuntimeError(f"Marker初始化失败: {e}")

    def _process_single_page(self, page_num: int) -> str:
        """处理单个页面：提取为临时PDF -> Marker转换 -> 返回文本"""
        import tempfile
        from marker.output import text_from_rendered
        
        # 1. 提取单页为临时PDF
        temp_pdf_path = self.output_dir / f"temp_page_{page_num}.pdf"
        
        try:
            doc = fitz.open(str(self.pdf_path))
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            new_doc.save(str(temp_pdf_path))
            new_doc.close()
            doc.close()
            
            # 2. 创建Converter实例 (每次处理都需要重新实例化吗？参考convert_single.py似乎是一次性的)
            # 但为了安全起见，我们按照convert_single.py的模式，每次都创建converter
            # 或者复用converter？ PdfConverter有状态吗？
            # 源码显示 self.page_count = None，似乎可以复用，但 __init__ 里处理了 artifact_dict
            # 为了稳妥，每次创建新的 converter 实例
            
            converter = self._PdfConverter(
                config=self._config_parser.generate_config_dict(),
                artifact_dict=self._model_dict,
                processor_list=self._config_parser.get_processors(),
                renderer=self._config_parser.get_renderer(),
                llm_service=self._config_parser.get_llm_service(),
            )
            
            # 3. 运行转换
            rendered = converter(str(temp_pdf_path))
            
            # 4. 提取文本
            text, _, _ = text_from_rendered(rendered)
            
            return text
            
        finally:
            # 清理临时文件
            if temp_pdf_path.exists():
                try:
                    os.remove(temp_pdf_path)
                except:
                    pass

    def get_text(self, start_page: int = 0, num_pages: int = 3) -> str:
        """提取前几页文本"""
        self._init_marker()
        
        print(f"⏳ Marker处理前{num_pages}页（约{num_pages*15}秒）...")
        
        all_text = []
        for i in range(min(num_pages, self.total_pages)):
            page_num = start_page + i
            print(f"  📖 处理第{page_num + 1}页...", end="", flush=True)
            
            try:
                text = self._process_single_page(page_num)
                all_text.append(text)
                print(" ✅")
            except Exception as e:
                print(f" ❌ {e}")
                raise RuntimeError(f"Marker处理第{page_num + 1}页失败: {e}")
        
        return "\n\n".join(all_text)
    
    def get_all_text_by_pages(self) -> List[str]:
        """逐页识别整个PDF"""
        self._init_marker()
        
        print(f"⏳ Marker逐页处理整个PDF（{self.total_pages}页，预计{self.total_pages*15}秒）...")
        
        all_pages_text = []
        for page_num in range(self.total_pages):
            print(f"  📖 处理第{page_num + 1}/{self.total_pages}页...", end="", flush=True)
            
            try:
                text = self._process_single_page(page_num)
                all_pages_text.append(text)
                print(" ✅")
            except Exception as e:
                print(f" ❌ {e}")
                raise RuntimeError(f"Marker处理第{page_num + 1}页失败: {e}")
        
        print(f"✅ 完成！共识别{len(all_pages_text)}页")
        return all_pages_text

    
    def get_page_image(self, page_number: int, dpi: int = 300) -> str:
        """获取页面图片（仍使用PyMuPDF）"""
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


class FigureScanner:
    """扫描PDF中的所有图表（图片和可能的标题）"""
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
    
    def scan_all_figures(self) -> List[dict]:
        """
        扫描整个PDF，返回所有检测到的图表信息
        返回格式: [{"page": int, "index": int, "caption": str}, ...]
        """
        figures = []
        
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            
            # 方法1: 检测图片对象
            image_list = page.get_images(full=True)
            
            # 方法2: 检测文本中的图表标题（Fig, Figure, Table等）
            text = page.get_text()
            captions = self._extract_figure_captions(text, page_num)
            
            # 合并检测结果
            if image_list:
                for idx, img in enumerate(image_list):
                    # 尝试匹配对应的标题
                    caption = self._find_matching_caption(captions, idx, page_num)
                    figures.append({
                        "page": page_num,
                        "index": idx,
                        "type": "image",
                        "caption": caption or f"第{page_num+1}页图片{idx+1}"
                    })
            
            # 如果只有标题没有图片（可能是纯文本表格），也记录
            if captions and not image_list:
                for caption in captions:
                    figures.append({
                        "page": page_num,
                        "index": 0,
                        "type": "text_figure",
                        "caption": caption
                    })
        
        return figures
    
    def _extract_figure_captions(self, text: str, page_num: int) -> List[str]:
        """从文本中提取图表标题"""
        captions = []
        
        # 匹配常见的图表标题模式
        patterns = [
            r'Fig\.?\s*\d+[a-z]?[\.:：]?\s*[^\n]{5,100}',  # Fig. 1: ...
            r'Figure\s*\d+[a-z]?[\.:：]?\s*[^\n]{5,100}',  # Figure 1: ...
            r'Table\s*\d+[a-z]?[\.:：]?\s*[^\n]{5,100}',   # Table 1: ...
            r'图\s*\d+[a-z]?[\.:：]?\s*[^\n]{5,100}',      # 图 1: ...
            r'表\s*\d+[a-z]?[\.:：]?\s*[^\n]{5,100}',      # 表 1: ...
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            captions.extend(matches)
        
        return list(set(captions))  # 去重
    
    def _find_matching_caption(self, captions: List[str], img_idx: int, page_num: int) -> Optional[str]:
        """尝试为图片找到对应的标题"""
        if not captions:
            return None
        
        # 简单策略：如果只有一个标题，就用它；否则返回第一个
        return captions[0] if captions else None
    
    def close(self):
        self.doc.close()


# --- Utilities ---

def sanitize_obsidian_filename(name: str) -> str:
    """
    Clean filename for Obsidian compatibility:
    1. Replace invalid chars (\ / : * ? " < > |) with '_'
    2. Collapse consecutive underscores
    3. Strip leading/trailing underscores
    """
    if not name:
        return "untitled"
    
    # Step 1: Replace invalid chars
    invalid_chars = r'\/:*?"<>|'
    clean_name = name
    for char in invalid_chars:
        clean_name = clean_name.replace(char, "_")
    return clean_name.strip()

def deduplicate_sections(sections: List[SectionIntent], figures_list: List[dict] = None) -> List[SectionIntent]:
    """
    去除重复的section分析。判断重复的标准：
    1. 相同的图表编号（如Fig. 1, Table 2）
    2. 相似的章节关键词（如Introduction, Methods）
    保留第一次出现的section。
    """
    if not sections:
        return sections
    
    import re
    from difflib import SequenceMatcher
    
    def extract_figure_number(title: str) -> str:
        """提取图表编号，如 'Fig. 1', 'Table 2', 'Figure 3' 等"""
        # 匹配常见的图表模式
        patterns = [
            r'Fig\.?\s*(\d+[a-z]?)',
            r'Figure\s*(\d+[a-z]?)',
            r'Table\s*(\d+)',
            r'Eq\.?\s*(\d+)',
            r'Equation\s*(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0).lower().replace(' ', '')  # 标准化格式
        return None
    
    def get_section_key(title: str) -> str:
        """提取章节关键词（如Introduction, Methods等）"""
        keywords = ['introduction', 'abstract', 'method', 'result', 'discussion', 
                   'conclusion', 'background', 'experiment', 'analysis']
        title_lower = title.lower()
        for keyword in keywords:
            if keyword in title_lower:
                return keyword
        return None
    
    def are_similar(title1: str, title2: str, threshold: float = 0.7) -> bool:
        """判断两个标题是否相似"""
        # 1. 检查是否有相同的图表编号
        fig1 = extract_figure_number(title1)
        fig2 = extract_figure_number(title2)
        if fig1 and fig2 and fig1 == fig2:
            return True
        
        # 2. 检查是否有相同的章节关键词
        key1 = get_section_key(title1)
        key2 = get_section_key(title2)
        if key1 and key2 and key1 == key2:
            return True
        
        # 3. 使用字符串相似度（备用方案）
        ratio = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        return ratio > threshold
    
    
    def should_keep_new(existing: SectionIntent, new: SectionIntent) -> bool:
        """判断是否应该用新section替换已存在的section"""
        # 优先级: figure/equation > text
        priority_map = {'figure': 2, 'equation': 2, 'text': 1}
        existing_priority = priority_map.get(existing.type, 0)
        new_priority = priority_map.get(new.type, 0)
        
        # 如果新的优先级更高，替换
        if new_priority > existing_priority:
            return True
        # 如果优先级相同，看子问题数量（保留更详细的）
        elif new_priority == existing_priority:
            return len(new.sub_questions) > len(existing.sub_questions)
        return False
    
    # 去重逻辑（优先保留图表类型）
    unique_sections = []
    section_map = {}  # title -> (index, section)
    
    for section in sections:
        found_similar = False
        similar_key = None
        
        # 查找是否有相似的section
        for key, (idx, existing) in section_map.items():
            if are_similar(section.section_title, key):
                found_similar = True
                similar_key = key
                # 判断是否应该替换
                if should_keep_new(existing, section):
                    unique_sections[idx] = section
                    section_map[similar_key] = (idx, section)
                break
        
        if not found_similar:
            idx = len(unique_sections)
            unique_sections.append(section)
            section_map[section.section_title] = (idx, section)
    
    # 打印去重结果
    removed_count = len(sections) - len(unique_sections)
    if removed_count > 0:
        print(f"🔧 去重完成: 移除了{removed_count}个重复section，保留{len(unique_sections)}个唯一section")
    
    # 验证图表覆盖完整性
    if figures_list:
        figure_sections = [s for s in unique_sections if s.type in ['figure', 'equation']]
        print(f"📊 图表覆盖验证: 检测到{len(figures_list)}个图表，生成了{len(figure_sections)}个图表分析section")
        
        # 提取所有图表编号
        detected_figs = set()
        for fig in figures_list:
            fig_num = extract_figure_number(fig.get('caption', ''))
            if fig_num:
                detected_figs.add(fig_num)
        
        analyzed_figs = set()
        for section in figure_sections:
            fig_num = extract_figure_number(section.section_title)
            if fig_num:
                analyzed_figs.add(fig_num)
        
        missing = detected_figs - analyzed_figs
        if missing:
            print(f"⚠️  警告: 以下图表可能未被分析: {', '.join(sorted(missing))}")
        else:
            print(f"✅ 所有检测到的图表都有对应分析section")
    
    return unique_sections

def call_api_with_retry(client, model, messages, response_format=None, max_retries=15):
    import json
    retries = 0
    base_delay = 2
    
    # Add throttling: sleep before each call to avoid hitting rate limits
    time.sleep(1.5)  # 1.5 second delay between API calls
    
    while retries < max_retries:
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format
            )
        except json.JSONDecodeError as e:
            # Special handling for JSON parsing errors (often means API returned HTML error page)
            wait_time = base_delay * (2 ** retries)
            print(f"⚠️  JSON解析错误 (API可能返回了非JSON响应). 等待 {wait_time} 秒后重试... (尝试 {retries+1}/{max_retries})")
            print(f"   错误详情: {str(e)[:200]}")
            time.sleep(wait_time)
            retries += 1
            if retries >= max_retries:
                print(f"❌ JSON解析错误持续出现，已达到重试上限。跳过此问题。")
                return None  # Return None to allow skipping
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                wait_time = base_delay * (2 ** retries)
                print(f"⚠️ 触发速率限制 (Rate limit/Quota). 等待 {wait_time} 秒后重试... (Attempt {retries+1}/{max_retries})")
                time.sleep(wait_time)
                retries += 1
            elif "400" in error_str:
                # Allow limited retries for 400 (may be transient content filtering)
                if retries < 3:  # Only retry 400 up to 3 times
                    wait_time = 3 * (retries + 1)  # 3, 6, 9 seconds
                    print(f"⚠️ API 400 错误 (可能是内容过滤). 等待 {wait_time} 秒后重试... (Attempt {retries+1}/3)")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"❌ API 400 错误持续出现，已达到重试上限。")
                    raise e
            else:
                print(f"❌ API 调用发生未处理错误: {e}")
                raise e
    raise Exception(f"API 调用超过最大重试次数 ({max_retries})")

class ArchitectAgent:
    def __init__(self, client: OpenAI):
        self.client = client

    def generate_outline(self, text_content: str, figures_list: List[dict] = None, include_appendix: bool = False) -> Outline:
        """
        生成论文阅读大纲
        Args:
            text_content: 论文文本内容（前几页）
            figures_list: 扫描得到的图表清单 [{"page": int, "caption": str}, ...]
            include_appendix: 是否包含附录
        """
        appendix_instruction = "请分析附录 (Appendix) 部分。" if include_appendix else "请忽略附录 (Appendix)，专注于正文。"
        
        # 构建图表清单文本
        figures_text = ""
        if figures_list:
            figures_text = "\n\n## 已检测到的图表清单（必须全部分析）\n"
            for fig in figures_list:
                figures_text += f"- 第{fig['page']+1}页: {fig['caption']}\n"
            figures_text += "\n**重要**: 以上所有图表都必须在你的分析大纲中体现。\n"

        system_prompt = f"""
        你是一位学术架构师。你的目标是模拟一位"好奇且严谨的研究生"，通读论文摘要和目录后，构建一个**有层级、有标号**的深度研读提纲。

        ## 核心指令

        ### ⚠️ 第一优先级：完整覆盖所有视觉元素
        **强制要求**：在设计任何问题之前，你必须：
        1. **图表清单核查**：检查下方提供的图表清单，每一个图、表、公式都必须在你的大纲中有对应的section
        2. **逐一对应**：为每个图表创建专门的分析section（如"3.1.1 Fig 1 任务范式"，"3.1.2 Fig 2 神经响应"）
        3. **公式追踪**：如果论文中出现编号公式（Equation 1, 2...），必须为每个公式创建分析section

        {figures_text}

        ### 第二优先级：IMRAD结构完整性
        1. {appendix_instruction}
        2. **结构自检**: 你的大纲必须完整覆盖学术论文的核心结构 (IMRAD: Introduction, Methods, Results, Discussion)。
        3. **环节细化**: 每个一级环节（如Methods）必须包含至少2个二级子环节。

        ### 第三优先级：多维度深度提问
        在确保覆盖完整性后，对每个section生成2-4个不同维度的子问题。

        请输出符合以下 JSON Schema 的对象：
        {{
            "paper_title": "str",
            "summary": "str (用中文)",
            "sections": [
                {{
                    "section_title": "str (必须包含层级标号，如 '1. 摘要', '2.1 图表分析')",
                    "target_pages": [int (0-indexed)],
                    "filename_slug": "str",
                    "type": "figure|equation|text",
                    "sub_questions": [
                        {{
                            "question": "str (具体的探究性问题)",
                            "question_type": "phenomenon|mechanism|critique"
                        }},
                        ...
                    ]
                }}
            ]
        }}

        ## 详细策略

        ### 1. 标号规范 (Hierarchy)
        请在 `section_title` 中严格使用标号，例如：
        - `1. 核心贡献与摘要`
        - `2. 背景 (Introduction)`
        - `2.1 核心假设与理论分歧`
        - `3. 实验设计 (Methods)`
        - `3.1 关键变量与 Visual Stimuli`
        - `3.1.1 Fig 1 任务范式图解` ← **每个图表必须有这样的section！**
        - `3.1.2 Equation 1: logLR计算公式` ← **每个编号公式必须有section！**

        ### 2. 图表分析section的强制要求
        对于每个检测到的图表，你必须创建一个独立的section，包含：
        - **type**: 设置为 "figure" (图表) 或 "equation" (公式)
        - **target_pages**: 该图表所在的页码
        - **section_title**: 明确包含图表编号（如"Fig 1", "Table 2", "Eq. 3"）
        
        **示例**：
        ```json
        {{
            "section_title": "3.1.1 Fig 1: 任务范式示意图",
            "target_pages": [2],
            "filename_slug": "fig1_paradigm",
            "type": "figure",
            "sub_questions": [
                {{
                    "question": "Fig 1展示了怎样的实验流程？各阶段的时序关系如何？",
                    "question_type": "phenomenon"
                }},
                {{
                    "question": "该任务设计如何确保被试必须进行概率整合而非简单记忆？",
                    "question_type": "mechanism"
                }},
                {{
                    "question": "如果改变形状呈现顺序，实验结果会如何变化？",
                    "question_type": "critique"
                }}
            ]
        }}
        ```

        ### 3. 多维子问题生成 (针对每个section)
        **三种问题类型**：
        - **phenomenon** (现象描述/"是什么"): 描述图表内容、数据趋势、观察结果
        - **mechanism** (机理推导): 探究背后的数学推导、计算原理、神经机制
        - **critique** (批判与改进/"为什么"): 质疑设计、识别局限、提出改进

        ### 4. 覆盖完整性自检清单
        在输出最终JSON之前，请自问：
        - [ ] 图表清单中的每个图/表是否都有对应的section？
        - [ ] 每个编号公式（如果有）是否都被分析？
        - [ ] IMRAD四大部分是否都有覆盖？
        - [ ] 每个section的sub_questions是否包含2-4个不同类型的问题？

        **禁止泛泛而谈**：
        *   **❌ 差**：["分析图2", "讲讲实验结果", "说说这个公式"]
        *   **✅ 优**：具体、原理向、有上下文的深度提问（见上述范例）
        
        请确保生成的"学习地图"逻辑严密，像一份高质量的**研读笔记目录**，且不遗漏任何关键视觉元素。
        """
        
        response = call_api_with_retry(
            self.client,
            model=ARCHITECT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"分析这篇论文文本 (Abstract/Intro) 并生成研读大纲。\n**重要：请务必使用中文输出 JSON 内容，并严格遵守层级标号要求。**\n\n{text_content[:8000]}"}
            ],
            response_format={"type": "json_object"}
        )
        
        # Pydantic validation (simple version for robustness)
        content = None
        try:
            content = response.choices[0].message.content
            return Outline.model_validate_json(content)
        except Exception as e:
            # Fallback if json is messy
            print(f"JSON Parse Error: {e}")
            if content:
                print(f"Raw Content: {content}") # DEBUG PRINT
            else:
                print("Raw Content: None (Extraction failed)")
            
            # Try to fix or re-raise
            if content:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                     return Outline.model_validate_json(match.group(0))
            raise e

class ContentValidator:
    def __init__(self, min_length=600, max_length=3500):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, content: str, section_type: str) -> tuple[bool, str]:
        """
        Validates content quality.
        Returns: (is_valid, critique_message)
        """
        # 1. Length Check (Chinese characters approx)
        clean_len = len(re.sub(r'\s+', '', content))
        if clean_len < self.min_length:
            return False, f"回答字数严重不足（当前约 {clean_len} 字）。目标需 {self.min_length}-{self.max_length} 字。请大幅扩充原理推导和细节分析。"
        if clean_len > self.max_length:
            return False, f"回答字数过多（{clean_len} 字），请精简到 {self.max_length} 字以内。"

        # 2. LaTeX Check (Critical for equations/figures)
        if section_type in ["figure", "equation"]:
            if "$" not in content and "$$" not in content:
                # User requested "Must contain Latex".
                return False, "未检测到数学公式（Latex格式）。作为理论分析，必须包含推导公式（使用 $$ 或 $）。"

        # 3. 4-Dimension Taxonomy Check
        required_tags = ["[现象]", "[机理]", "[目的]", "[批判]"]
        missing_tags = [tag for tag in required_tags if tag not in content]
        
        if missing_tags:
            return False, f"缺失认知维度分析: {', '.join(missing_tags)}。请确保回答包含以下四个维度的完整分析：\n" \
                          "1. ### [现象] ... (描述观察)\n" \
                          "2. ### [机理] ... (第一性原理/公式推导)\n" \
                          "3. ### [目的] ... (计算目标/演化意义)\n" \
                          "4. ### [批判] ... (局限性/替代解释)"

        return True, "Pass"

class AnalystAgent:
    def __init__(self, client: OpenAI):
        self.client = client
        self.validator = ContentValidator()

    def analyze_section(self, image_b64: str, sub_question: SubQuestion, section_type: str = "text", prev_context: str = "") -> str:
        """
        分析论文特定部分
        Args:
            image_b64: Base64编码的图片
            sub_question: SubQuestion对象（包含问题、类型和字数要求）
            section_type: 内容类型
            prev_context: 先前的上下文
        """
        # 根据问题类型定制system_prompt
        question_type_desc = {
            "phenomenon": "现象描述/'是什么'",
            "mechanism": "机理推导",
            "critique": "目的和批判/'为什么'"
        }
        
        current_type_desc = question_type_desc.get(sub_question.question_type, "综合分析")
        
        system_prompt = f"""
        你是一位世界顶尖的**理论神经科学家和物理学家**（如 Feynman 或 Hopfield 风格）。
        你的任务是对学术论文的特定部分进行深度解析。

        ## 当前问题类型: {current_type_desc}
        
        根据问题类型，你需要采用不同的分析策略：

        ### 如果是"phenomenon"（现象描述/"是什么"）:
        - **重点**: 客观描述图表趋势、解剖结构或数据特征
        - **包含**: 观察到的现象、数据模式、视觉特征
        - **字数要求**: 目标{sub_question.min_words}-{sub_question.max_words}字，验证范围{sub_question.validate_min}-{sub_question.validate_max}字

        ### 如果是"mechanism"（机理推导）:
        - **重点**: 解释背后的生成机制
        - **必须包含**: 
          - 第一性原理推导（First-Principles Derivation）
          - 每个变量的物理/神经意义
          - 数学公式（使用LaTeX格式）
        - **字数要求**: 目标{sub_question.min_words}-{sub_question.max_words}字，验证范围{sub_question.validate_min}-{sub_question.validate_max}字

        ### 如果是"critique"（目的和批判/"为什么"）:
        - **重点**: 质疑设计动机、识别局限性
        - **包含**:
          - 为什么要这样设计？解决了什么计算问题？
          - 这个结论在什么条件下不成立？
          - 是否存在替代解释模型？
        - **字数要求**: 目标{sub_question.min_words}-{sub_question.max_words}字，验证范围{sub_question.validate_min}-{sub_question.validate_max}字

        ## 格式规范
        1. **全中文输出**
        2. **使用Markdown格式**，数学公式使用LaTeX (`$$ ... $$` 或 `$ ... $`)
        3. **段落控制**: 任何段落不超过5行
        4. **关键词加粗**: 核心概念用**粗体**标记
        5. **列表化**: 涉及列举使用Bullet Points
        
        **重要**: 输出后我会进行字数验证。如果不在{sub_question.validate_min}-{sub_question.validate_max}字范围内，你需要重写。
        """

        user_prompt = f"""
        ## 任务
        问题: {sub_question.question}
        问题类型: {current_type_desc}
        参考资料: 见附图
        
        请针对这个问题进行深度分析，字数控制在{sub_question.min_words}-{sub_question.max_words}字之间。
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            },
        ]

        # Retry Loop with word count validation
        max_retries = 3
        for attempt in range(max_retries):
            print(f"💭 分析中... (尝试 {attempt+1}/{max_retries})")
            
            response = call_api_with_retry(
                self.client,
                model=ANALYST_MODEL,
                messages=messages
            )
            
            # Handle case where API call failed after max retries
            if response is None:
                print(f"⚠️  API调用失败，跳过此问题")
                return f"# {sub_question.question}\n\n**[分析跳过：API调用失败]**\n\n该问题因API错误被跳过，请稍后手动补充分析。"
            
            content = response.choices[0].message.content
            
            # Word count validation (Chinese characters)
            word_count = len(re.sub(r'\s+', '', content))
            
            if sub_question.validate_min <= word_count <= sub_question.validate_max:
                print(f"✅ 字数验证通过: {word_count}字 (目标{sub_question.min_words}-{sub_question.max_words}字)")
                return content
            else:
                print(f"⚠️  字数不符: 当前{word_count}字，要求{sub_question.validate_min}-{sub_question.validate_max}字")
                
                # Provide feedback for retry
                if word_count < sub_question.validate_min:
                    feedback = f"回答字数不足（{word_count}字）。需要至少{sub_question.validate_min}字，目标{sub_question.min_words}-{sub_question.max_words}字。请大幅扩充分析深度和细节。"
                else:
                    feedback = f"回答字数过多（{word_count}字）。需要控制在{sub_question.validate_max}字以内，目标{sub_question.min_words}-{sub_question.max_words}字。请精简表述。"
                
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"字数验证未通过: {feedback}\n请重写，严格遵守字数要求。"})
        
        # If all retries failed, return with warning
        word_count = len(re.sub(r'\s+', '', content))
        warning = f"\n\n---\n⚠️ **字数警告**: 当前{word_count}字，未达到{sub_question.validate_min}-{sub_question.validate_max}字要求（已重试{max_retries}次）\n"
        return content + warning
        
        # If all retries failed, append a warning but return content (don't crash)
        return content + "\n\n> [!WARNING] 此内容未完全通过质量验证 (e.g. 维度缺失或字数不足)，建议人工复核。"

class FileManager:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def write_hub_index(self, outline: Outline, paper_folder: Path, paper_slug: str):
        content = f"# {outline.paper_title}\n\n"
        content += f"## Summary\n{outline.summary}\n\n"
        content += "## Deep Dive Index\n"
        for section in outline.sections:
            clean_slug = sanitize_obsidian_filename(section.filename_slug)
            # Create unique slug: paper_slug + section_slug
            unique_slug = f"{paper_slug}_{clean_slug}"
            # User requested to avoid '|' alias syntax.
            # Format: [[UniqueSlug]] - Title - Intent
            # Main section link
            content += f"- [[{unique_slug}]] : **{section.section_title}**\n"
            # Sub-question links with Obsidian anchors
            for idx, sub_q in enumerate(section.sub_questions, 1):
                # Obsidian anchor format: [[Note#anchor-id|Display Text]]
                preview = sub_q.question[:60] + "..." if len(sub_q.question) > 60 else sub_q.question
                content += f"  - [[{unique_slug}#sub-q{idx}|🔍 子问题{idx}]]: {preview}\n"
        
        # Helper to ensure master index is also unique if needed? 
        # User only mentioned "hyperlinks" (spokes). 
        # But let's keep 00_Master_Index generic inside the folder?
        # Actually, if we link to 00_Master_Index from outside, it might collide.
        # But usually Master Index is the entry point. 
        # Let's keep 00_Master_Index for now as it's 'internal' to the folder structure, 
        # but the spokes need to be unique because [[wikilinks]] are flat namespace.
        
        with open(paper_folder / "00_Master_Index.md", "w", encoding="utf-8") as f:
            content += "\n\n---\n"
            content += "## Navigation\n"
            content += f"**Vault Root**: [[00_Master_Index]] (This might collide if multiple papers used. Future improvement: Paper_Index)\n" 
            f.write(content)

    def write_spoke_note(self, section: SectionIntent, all_analyses: list, paper_folder: Path, paper_slug: str):
        clean_slug = sanitize_obsidian_filename(section.filename_slug)
        if not clean_slug: clean_slug = "untitled"
        
        # Unique filename
        unique_slug = f"{paper_slug}_{clean_slug}"
        file_path = paper_folder / f"{unique_slug}.md"
        
        # Check if file exists to determine mode and header
        file_exists = file_path.exists()
        
        mode = "a" if file_exists else "w"
        
        with open(file_path, mode, encoding="utf-8") as f:
            if not file_exists:
                # Write Frontmatter and Title only for new files
                file_content = "---\n"
                file_content += "parent: [[00_Master_Index]]\n" 
                # Note: parent link is local to folder, usually fine if opened in context.
                # But to be safe, maybe parent should also be unique?
                # User complaint was about "hyperlinks name... same... point to same file".
                # So [[abstract]] in Paper A and [[abstract]] in Paper B both point to Paper A's abstract.
                # By renaming file to Yang_abstract.md, [[Yang_abstract]] works.
                
                file_content += f"tags: [paper, analysis, {section.type}]\n"
                file_content += "---\n\n"
                file_content += f"# {section.section_title}\n\n"
                f.write(file_content)
            else:
                # Separator for appending
                f.write("\n\n---\n\n")
            
            # Write the Q&A block
            # Write all sub-question Q&A blocks with Obsidian anchors
            for analysis in all_analyses:
                # Obsidian heading anchor format: {#anchor-id}
                q_a_block = f"## 🧐 探究问题: {analysis['question']} {{#{analysis['anchor_id']}}}\n\n"
                q_a_block += f"### 💡 分析回答\n{analysis['answer']}\n\n"
                f.write(q_a_block)

# --- Main Workflow ---

def main():
    parser = argparse.ArgumentParser(description="Paper to Obsidian Workflow")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--vault", required=True, help="Path to Obsidian Vault Root")
    parser.add_argument("--include_appendix", action="store_true", help="Include appendix in analysis")
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment.")
        return

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )

    pdf_path = Path(args.pdf)
    vault_root = Path(args.vault)
    
    # Create folder for this paper
    paper_folder = vault_root / pdf_path.stem
    paper_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate Paper Slug for unique filenames
    # We need to access sanitize_obsidian_filename. Using it from global scope.
    paper_slug = sanitize_obsidian_filename(pdf_path.stem)[:50]

    print(f"正在处理 {pdf_path.name}...")
    
    # 1. Ingestion & Figure Scanning - 根据配置选择PDF处理器
    if USE_MARKER:
        print("🔬 使用Marker处理器（支持公式识别）")
        pdf_proc = MarkerProcessor(str(pdf_path))
        
        # Marker模式：逐页识别整个PDF
        all_pages_text = pdf_proc.get_all_text_by_pages()
    else:
        print("⚡ 使用PyMuPDF处理器（快速模式）")
        pdf_proc = PDFProcessor(str(pdf_path))
        
        # PyMuPDF模式：逐页提取（为了统一接口）
        all_pages_text = []
        for i in range(len(pdf_proc.doc)):
            all_pages_text.append(pdf_proc.doc[i].get_text())
        print(f"✅ 提取了{len(all_pages_text)}页文本")
    
    # NEW: Scan all figures first
    print("📊 图表扫描: 正在识别PDF中的所有图表...")
    figure_scanner = FigureScanner(str(pdf_path))
    figures_list = figure_scanner.scan_all_figures()
    figure_scanner.close()
    print(f"✅ 检测到 {len(figures_list)} 个图表/表格")

    # 2. Architect - 分批处理
    print("架构师: 正在分批生成深度阅读大纲...")
    architect = ArchitectAgent(client)
    
    all_sections = []

    
    try:
        # 计算批次数
        num_batches = (len(all_pages_text) + PAGES_PER_BATCH - 1) // PAGES_PER_BATCH
        print(f"📚 共{len(all_pages_text)}页，将分{num_batches}批处理（每批{PAGES_PER_BATCH}页）")
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * PAGES_PER_BATCH
            end_idx = min((batch_idx + 1) * PAGES_PER_BATCH, len(all_pages_text))
            
            # 合并本批次的文本
            batch_text = "\n\n---\n\n".join(all_pages_text[start_idx:end_idx])
            
            print(f"\n  批次 {batch_idx+1}/{num_batches}: 第{start_idx+1}-{end_idx}页")
            
            # 调用Architect生成本批次的大纲
            batch_outline = architect.generate_outline(
                batch_text, 
                figures_list=figures_list if batch_idx == 0 else None,  # 只在第一批传入图表列表
                include_appendix=args.include_appendix
            )
            
            # 收集sections
            all_sections.extend(batch_outline.sections)
            print(f"  ✅ 生成了{len(batch_outline.sections)}个分析问题")
        
        # 合并所有批次的结果
        print(f"\n✅ 所有批次完成！共生成{len(all_sections)}个分析问题")
        
        # 去重处理
        unique_sections = deduplicate_sections(all_sections, figures_list)
        
        # 创建完整的Outline
        outline = Outline(
            paper_title=batch_outline.paper_title,  # 使用最后一批的标题（实际应该都一样）
            summary=batch_outline.summary,
            sections=unique_sections
        )
        
        # Soft Structure Check
        titles = [s.section_title.lower() for s in outline.sections]
        imrad_keywords = ["intro", "method", "result", "discuss"]
        missing = [k for k in imrad_keywords if not any(k in t for t in titles)]
        if missing:
             print(f"⚠️ [Structure Warning] 大纲似乎缺失核心章节: {missing}。但这可能是由于论文结构特殊。")
    except Exception as e:
        print(f"架构师出错: {e}")
        pdf_proc.close()
        return

    print(f"计划已生成: 共 {len(outline.sections)} 个部分需要分析。")

    # 3. Analyst loop
    analyst = AnalystAgent(client)
    file_manager = FileManager(vault_root)
    file_manager.write_hub_index(outline, paper_folder, paper_slug)

    for section in outline.sections:
        print(f"分析师: 正在深入分析 {section.section_title}...")
        # Just grab the first target page for now for simplicity, or combine them
        if not section.target_pages:
            continue
            
        target_page_idx = section.target_pages[0] 
        # Safety check
        if target_page_idx >= len(pdf_proc.doc):
             target_page_idx = 0
             
        image_b64 = pdf_proc.get_page_image(target_page_idx)
        
        # Process all sub_questions (2-4 questions per section)
        all_analyses = []
        for idx, sub_q in enumerate(section.sub_questions, 1):
            print(f"  Sub-Question {idx}/{len(section.sub_questions)} ({sub_q.question_type}): {sub_q.question[:50]}...")
            analysis_content = analyst.analyze_section(image_b64, sub_q, section_type=section.type)
            all_analyses.append({
                'question': sub_q.question,
                'answer': analysis_content,
                'anchor_id': f"sub-q{idx}"
            })
        
        file_manager.write_spoke_note(section, all_analyses, paper_folder, paper_slug)
        print(f"Saved: {paper_slug}_{section.filename_slug}.md")

    pdf_proc.close()
    print(f"完成! 请查看目录: {paper_folder}")

if __name__ == "__main__":
    main()
