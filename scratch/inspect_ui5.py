from PIL import Image

im = Image.open(r"d:\sinwoo\error\UI5-0912.png")
print("Image size:", im.size)
# Let's inspect vertical slice in the middle of the image
w, h = im.size
mid_x = w // 2
colors = []
for y in range(h):
    r, g, b = im.getpixel((mid_x, y))[:3]
    colors.append((y, (r, g, b)))

# Find where the card ends and where the footer text appears
# Card footer is white/gray (#EEF2F6 or similar)
# Background of visual-card-box is #F8FAFC (248, 250, 252)
for y in range(200, h, 10):
    print(f"y={y}: {colors[y][1]}")
