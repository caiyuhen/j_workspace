from PIL import Image, ImageDraw, ImageFont
import os

def create_image():
    # Create a white image
    img = Image.new('RGB', (400, 200), color='white')
    d = ImageDraw.Draw(img)
    
    # Draw some text
    # Note: Default font might not support Chinese, but let's try english first
    try:
        # Try to use a system font if possible, otherwise default
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    d.text((50, 50), "Hello World", fill=(0, 0, 0), font=font)
    d.text((50, 100), "OCR Test 123", fill=(0, 0, 0), font=font)
    
    img.save('test_image.png')
    print("Test image created: test_image.png")

if __name__ == "__main__":
    create_image()
