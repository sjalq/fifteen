from PIL import Image, ImageDraw
import os

# Create a simple icon with a white square on a blue background
icon = Image.new("RGBA", (256, 256), color=(0, 120, 215))
draw = ImageDraw.Draw(icon)
# Draw a white square in the middle
draw.rectangle([(64, 64), (192, 192)], fill=(255, 255, 255))

# Save as ICO
icon.save("icon.ico")

print(f"Icon created at {os.path.abspath('icon.ico')}") 