from PIL import Image, ImageDraw, ImageFont
import os

def create_blood_routine_image():
    width = 1000
    height = 800
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    
    font_path = "C:\\Windows\\Fonts\\simhei.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 24)
        font_text = ImageFont.truetype(font_path, 20)
        font_small = ImageFont.truetype(font_path, 16)
    except IOError:
        font_header = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Title
    d.text((300, 20), "北京中医药大学第三附属医院检验报告单", fill=(0, 0, 0), font=font_header)
    d.text((50, 60), "姓名: 潘月武  年龄: 68岁  性别: 男", fill=(0, 0, 0), font=font_text)
    
    # Draw Table Header (Left and Right)
    header_y = 120
    d.text((50, header_y), "检验项目", fill=(0, 0, 0), font=font_text)
    d.text((200, header_y), "结果", fill=(0, 0, 0), font=font_text)
    d.text((300, header_y), "参考范围", fill=(0, 0, 0), font=font_text)
    d.text((450, header_y), "单位", fill=(0, 0, 0), font=font_text)
    
    d.text((550, header_y), "检验项目", fill=(0, 0, 0), font=font_text)
    d.text((700, header_y), "结果", fill=(0, 0, 0), font=font_text)
    d.text((800, header_y), "参考范围", fill=(0, 0, 0), font=font_text)
    d.text((950, header_y), "单位", fill=(0, 0, 0), font=font_text)
    
    d.line((0, header_y + 30, width, header_y + 30), fill=(0, 0, 0))
    
    # Draw Content
    start_y = 160
    row_height = 30
    
    # Left Column Data
    left_data = [
        ("WBC", "1.63", "3.50~9.50", "10^9/L"),
        ("RBC", "4.16", "4.30~5.80", "10^12/L"),
        ("HGB", "121", "130~175", "g/L"),
        ("PLT", "89", "125~350", "10^9/L")
    ]
    
    for i, (name, res, ref, unit) in enumerate(left_data):
        y = start_y + i * row_height
        d.text((50, y), name, fill=(0, 0, 0), font=font_text)
        d.text((200, y), res, fill=(0, 0, 0), font=font_text)
        d.text((300, y), ref, fill=(0, 0, 0), font=font_text)
        d.text((450, y), unit, fill=(0, 0, 0), font=font_text)

    # Right Column Data
    right_data = [
        ("LYMPH%", "0.63", "1.10~3.20", "10^9/L"),
        ("MONO#", "0.34", "0.10~0.60", "10^9/L"),
        ("EO#", "0.01", "0.02~0.52", "10^9/L")
    ]
    
    for i, (name, res, ref, unit) in enumerate(right_data):
        y = start_y + i * row_height
        d.text((550, y), name, fill=(0, 0, 0), font=font_text)
        d.text((700, y), res, fill=(0, 0, 0), font=font_text)
        d.text((800, y), ref, fill=(0, 0, 0), font=font_text)
        d.text((950, y), unit, fill=(0, 0, 0), font=font_text)

    # Draw Graphs (simulated with text)
    graph_y = 400
    d.text((50, graph_y), "HPL Graph Area", fill=(0, 0, 0), font=font_text)
    d.text((300, graph_y), "HRB Graph Area", fill=(0, 0, 0), font=font_text)
    
    # Draw Footer
    footer_y = 600
    d.text((50, footer_y), "标本状态: 正常  备注: ※危急值报告单※", fill=(0, 0, 0), font=font_text)
    d.text((50, footer_y + 40), "送检医生: XX  检验者: XX  审核者: XX  报告时间: 2025-12-10", fill=(0, 0, 0), font=font_text)
    
    img.save('test_blood_routine.png')
    print("Test blood routine image created: test_blood_routine.png")

if __name__ == "__main__":
    create_blood_routine_image()
