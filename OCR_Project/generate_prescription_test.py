from PIL import Image, ImageDraw, ImageFont
import os

def create_prescription_image():
    # Create a white image
    width = 800
    height = 1000
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Load fonts (using default if custom font not found, but trying to use a system font for Chinese)
    try:
        font_title = ImageFont.truetype("msyh.ttc", 30)
        font_text = ImageFont.truetype("msyh.ttc", 20)
        font_small = ImageFont.truetype("msyh.ttc", 16)
    except:
        # Fallback for linux/other envs if msyh not found
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Header
    draw.text((300, 50), "某某附属医院", fill=(0, 0, 0), font=font_title)
    draw.text((320, 100), "处方笺", fill=(0, 0, 0), font=font_title)
    
    # Draw Patient Info
    draw.text((50, 160), "姓名: 张三", fill=(0, 0, 0), font=font_text)
    draw.text((250, 160), "性别: 男", fill=(0, 0, 0), font=font_text)
    draw.text((400, 160), "年龄: 35岁", fill=(0, 0, 0), font=font_text)
    draw.text((600, 160), "日期: 2025-12-12", fill=(0, 0, 0), font=font_text)
    
    draw.line((50, 200, 750, 200), fill=(0, 0, 0), width=2)
    
    # Draw Prescription Body (Rp)
    draw.text((50, 220), "Rp", fill=(0, 0, 0), font=font_title)
    
    # Drug 1
    draw.text((80, 270), "1. 阿莫西林胶囊", fill=(0, 0, 0), font=font_text)
    draw.text((400, 270), "0.5g*24粒", fill=(0, 0, 0), font=font_text)
    draw.text((600, 270), "x 2盒", fill=(0, 0, 0), font=font_text)
    draw.text((100, 300), "用法: 口服, 每次0.5g, 每日3次", fill=(0, 0, 0), font=font_small)
    
    # Drug 2
    draw.text((80, 340), "2. 布洛芬缓释胶囊", fill=(0, 0, 0), font=font_text)
    draw.text((400, 340), "0.3g*20粒", fill=(0, 0, 0), font=font_text)
    draw.text((600, 340), "x 1盒", fill=(0, 0, 0), font=font_text)
    draw.text((100, 370), "用法: 口服, 必要时, 每次1粒", fill=(0, 0, 0), font=font_small)

    # Drug 3 (Complex name)
    draw.text((80, 410), "3. 复方甘草片", fill=(0, 0, 0), font=font_text)
    draw.text((600, 410), "x 1瓶", fill=(0, 0, 0), font=font_text)
    draw.text((100, 440), "用法: 口服, 每次3片, 每日3次", fill=(0, 0, 0), font=font_small)

    draw.line((50, 800, 750, 800), fill=(0, 0, 0), width=2)
    
    # Footer
    draw.text((50, 820), "医师: 李四", fill=(0, 0, 0), font=font_text)
    draw.text((400, 820), "审核: 王五", fill=(0, 0, 0), font=font_text)

    # Save
    image.save("test_prescription.png")
    print("Created test_prescription.png")

if __name__ == "__main__":
    create_prescription_image()
