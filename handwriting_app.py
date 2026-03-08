import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from handright import Template, handwrite
import io
import os
import docx
from pypdf import PdfReader
import zipfile

# 设置页面配置
st.set_page_config(page_title="中文手写笔记生成器", page_icon="✍️", layout="wide")

def read_file_content(uploaded_file):
    """读取不同格式的文件内容"""
    content = ""
    try:
        if uploaded_file.name.endswith('.txt'):
            content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"解析文件失败: {str(e)}")
    return content

def on_file_upload():
    """回调函数：处理文件上传"""
    uploaded_file = st.session_state.uploaded_file_key
    if uploaded_file is not None:
        content = read_file_content(uploaded_file)
        if content:
            st.session_state.text_content = content

def create_lined_paper(width, height, line_spacing=60, margin=50, line_color=(180, 180, 200), bg_color=(255, 255, 240)):
    """生成带有横线的背景"""
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    # Draw horizontal lines
    for y in range(margin + line_spacing, height - margin, line_spacing):
        draw.line([(margin, y), (width - margin, y)], fill=line_color, width=1)
    # Draw a vertical margin line
    draw.line([(margin, margin), (margin, height - margin)], fill=(255, 100, 100), width=2)
    return img

def get_system_fonts():
    """获取可用中文字体 (系统字体 + 项目内置字体)"""
    fonts = {}
    
    # 1. 扫描项目内置字体 (fonts 目录)
    local_fonts_dir = "fonts"
    if os.path.exists(local_fonts_dir):
        for f in os.listdir(local_fonts_dir):
            if f.lower().endswith(('.ttf', '.otf', '.ttc')):
                fonts[f"内置: {f}"] = os.path.join(local_fonts_dir, f)

    # 2. 扫描 Windows 系统字体 (仅在本地运行时有效)
    system_fonts = {
        "系统: 楷体": "C:/Windows/Fonts/simkai.ttf",
        "系统: 仿宋": "C:/Windows/Fonts/simfang.ttf",
        "系统: 宋体": "C:/Windows/Fonts/simsun.ttc",
        "系统: 黑体": "C:/Windows/Fonts/simhei.ttf",
        "系统: 微软雅黑": "C:/Windows/Fonts/msyh.ttc",
    }
    # 过滤掉不存在的系统字体
    for name, path in system_fonts.items():
        if os.path.exists(path):
            fonts[name] = path
            
    return fonts

def main():
    st.title("✍️ 中文手写笔记生成器")
    st.markdown("通过调整参数，生成逼真的中文手写效果图片。")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("1. 内容设置")
        
        # 初始化 session_state
        if 'text_content' not in st.session_state:
            st.session_state.text_content = """DeepScript 项目笔记

虽然 DeepScript 主要针对英文，
但我们可以用这个工具生成中文手写！

支持自定义字体、背景和扰动参数。
让你的数字笔记看起来更有温度。"""

        # 文件上传区域
        st.file_uploader(
            "导入文档 (支持 txt, docx, pdf)", 
            type=['txt', 'docx', 'pdf'], 
            key="uploaded_file_key",
            on_change=on_file_upload
        )
        
        text = st.text_area("输入文字内容", value=st.session_state.text_content, height=300)
        
        # 当 text_area 修改时，更新 session_state
        if text != st.session_state.text_content:
            st.session_state.text_content = text

        st.header("2. 字体设置")
        font_source = st.radio("字体来源", ["系统字体", "上传字体文件"])
        
        font_path = None
        if font_source == "系统字体":
            system_fonts = get_system_fonts()
            selected_font_name = st.selectbox("选择字体", list(system_fonts.keys()))
            font_path = system_fonts.get(selected_font_name)
        else:
            uploaded_font = st.file_uploader("上传 .ttf 或 .otf 字体文件", type=["ttf", "otf", "ttc"])
            if uploaded_font:
                # Save uploaded font to a temporary file
                font_path = f"temp_font_{uploaded_font.name}"
                with open(font_path, "wb") as f:
                    f.write(uploaded_font.getbuffer())

        font_size = st.slider("字体大小", 20, 100, 50)
        
        st.header("3. 背景设置")
        bg_source = st.radio("背景来源", ["生成横线纸", "上传背景图"])
        
        background = None
        if bg_source == "生成横线纸":
            bg_width = st.number_input("宽度", 400, 2000, 800)
            bg_height = st.number_input("高度", 400, 3000, 1000)
            line_spacing = st.slider("行间距 (背景)", 40, 200, 80)
            background = create_lined_paper(bg_width, bg_height, line_spacing)
        else:
            uploaded_bg = st.file_uploader("上传背景图片", type=["png", "jpg", "jpeg"])
            if uploaded_bg:
                background = Image.open(uploaded_bg)
                # 确保背景是 RGB 模式
                if background.mode != 'RGB':
                    background = background.convert('RGB')

        st.header("4. 扰动参数 (关键!)")
        with st.expander("展开高级设置", expanded=True):
            line_spacing_param = st.slider("行间距 (排版)", 40, 200, 80, help="控制文字生成的行高，建议与背景行高一致")
            word_spacing = st.slider("字间距", 0, 50, 5)
            
            st.markdown("---")
            st.caption("随机扰动程度 (值越大越潦草)")
            font_size_sigma = st.slider("字体大小扰动", 0, 10, 3)
            word_spacing_sigma = st.slider("字间距扰动", 0, 10, 3)
            line_spacing_sigma = st.slider("行间距扰动", 0, 10, 2)
            perturb_x_sigma = st.slider("笔画水平抖动", 0, 5, 2)
            perturb_y_sigma = st.slider("笔画垂直抖动", 0, 5, 2)
            perturb_theta_sigma = st.slider("笔画旋转抖动", 0.00, 0.20, 0.05, step=0.01)

    with col2:
        st.header("预览结果")
        
        if st.button("🚀 生成笔记", type="primary"):
            if not font_path:
                st.error("请选择或上传一个有效的字体文件！")
            elif not background:
                st.error("请选择或上传一个有效的背景图片！")
            else:
                try:
                    with st.spinner("正在书写中..."):
                        # 配置模板
                        template = Template(
                            background=background,
                            font=ImageFont.truetype(font_path, size=font_size),
                            line_spacing=line_spacing_param,
                            fill=(0, 0, 0), # 黑色
                            left_margin=80,
                            top_margin=100,
                            right_margin=80,
                            bottom_margin=80,
                            word_spacing=word_spacing,
                            
                            line_spacing_sigma=line_spacing_sigma,
                            font_size_sigma=font_size_sigma,
                            word_spacing_sigma=word_spacing_sigma,
                            perturb_x_sigma=perturb_x_sigma,
                            perturb_y_sigma=perturb_y_sigma,
                            perturb_theta_sigma=perturb_theta_sigma,
                        )
                        
                        # 生成
                        images = list(handwrite(text, template))
                        
                        # 显示结果和下载选项
                        st.success(f"生成成功！共 {len(images)} 页")
                        
                        # 创建下载区域
                        download_col1, download_col2 = st.columns(2)
                        
                        # 1. 导出为 PDF
                        pdf_buffer = io.BytesIO()
                        if len(images) > 0:
                            # 将 PIL Image 转换为 RGB 模式（如果是 RGBA）以兼容 PDF 保存
                            pdf_images = [img.convert('RGB') for img in images]
                            pdf_images[0].save(
                                pdf_buffer, "PDF", resolution=100.0, save_all=True, append_images=pdf_images[1:]
                            )
                            with download_col1:
                                st.download_button(
                                    label="📄 下载全部为 PDF",
                                    data=pdf_buffer.getvalue(),
                                    file_name="handwriting_note.pdf",
                                    mime="application/pdf",
                                    type="primary"
                                )

                        # 2. 导出为 ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for i, img in enumerate(images):
                                img_byte_arr = io.BytesIO()
                                img.save(img_byte_arr, format='PNG')
                                zf.writestr(f"page_{i+1}.png", img_byte_arr.getvalue())
                        
                        with download_col2:
                            st.download_button(
                                label="📦 下载全部为 ZIP",
                                data=zip_buffer.getvalue(),
                                file_name="handwriting_images.zip",
                                mime="application/zip",
                            )

                        st.markdown("---")
                        st.markdown("### 预览")
                        
                        # 显示每页预览
                        for i, img in enumerate(images):
                            with st.expander(f"第 {i+1} 页", expanded=True):
                                st.image(img, use_column_width=True)
                                
                                # 提供单页下载
                                buf = io.BytesIO()
                                img.save(buf, format="PNG")
                                byte_im = buf.getvalue()
                                
                                st.download_button(
                                    label=f"⬇️ 下载本页 (PNG)",
                                    data=byte_im,
                                    file_name=f"handwriting_page_{i+1}.png",
                                    mime="image/png",
                                    key=f"dl_btn_{i}"
                                )
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")
                    st.warning("如果提示字体错误，请尝试使用系统自带的'楷体'或上传有效的字体文件。")

if __name__ == "__main__":
    main()
