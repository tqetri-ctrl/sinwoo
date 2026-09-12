from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QColor, QPainter, QTextDocument
from PyQt6.QtCore import QUrl
import sys

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(750, 700)

img = QImage(960, 450, QImage.Format.Format_ARGB32)
img.fill(QColor(30, 58, 138))
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("test.png"), img)

# Case 1: width="620" only
html1 = '<div style="background: #eef;"><p>Top</p><img src="test.png" width="620"><p>Bottom text</p></div>'
tb.setHtml(html1)
tb.show()
tb.grab().save("scratch/test_layout_case1.png")

# Case 2: Exact width and height matching aspect ratio or native
# 620 * (450 / 960) = 290.625 -> 291
html2 = '<div style="background: #eef;"><p>Top</p><img src="test.png" width="620" height="291"><p>Bottom text</p></div>'
tb.setHtml(html2)
tb.grab().save("scratch/test_layout_case2.png")

# Case 3: Native 640x360 image with no width/height attribute in HTML
img_native = QImage(640, 360, QImage.Format.Format_ARGB32)
img_native.fill(QColor(30, 58, 138))
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("native.png"), img_native)
html3 = '<div style="background: #eef; text-align: center;"><p style="margin:0 0 6px 0;">Top</p><img src="native.png" style="display:block; margin:0 auto;"><p style="margin:6px 0 0 0;">Bottom text</p></div>'
tb.setHtml(html3)
tb.grab().save("scratch/test_layout_case3.png")

print("Generated cases")
