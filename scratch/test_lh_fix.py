import sys
sys.path.insert(0, '.')
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QTextDocument
from PyQt6.QtCore import QUrl
from ui.styles import generate_blog_preview_html

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(720, 800)

img = QImage(620, 400, QImage.Format.Format_ARGB32)
img.fill(0xFF1E3A8A)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl('chart_preview.png'), img)

full_html = generate_blog_preview_html('Title', '[추천 차트: 도마변동 5구역]', [], True, False)

# Test with .visual-card-box { line-height: 1.0; } or removing line-height from body
test_html = full_html.replace(
    ".placeholder-box {",
    ".visual-card-box { line-height: 1.1; margin: 12px 0; }\n        .placeholder-box {"
).replace(
    "line-height: 1.85;",
    ""
)
# And set line-height on p only
test_html = test_html.replace(
    ".blog-content p {",
    ".blog-content p { line-height: 1.8;\n"
)

tb.setHtml(test_html)
tb.document().setTextWidth(720)
b2 = tb.document().findBlockByNumber(2)
b3 = tb.document().findBlockByNumber(3)
l2 = b2.layout()
l3 = b3.layout()
pos2 = l2.position().y()
h2 = l2.boundingRect().height()
pos3 = l3.position().y()

print(f"b2 y={pos2:.1f}, h={h2:.1f}, ends at {pos2+h2:.1f}")
print(f"b3 y={pos3:.1f}")
print(f"GAP = {pos3 - (pos2 + h2):.1f} px!")

tb.grab().save("scratch/test_line_height_fixed.png")
print("Saved scratch/test_line_height_fixed.png")
