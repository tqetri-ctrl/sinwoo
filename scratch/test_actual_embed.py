from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QColor, QTextDocument
from PyQt6.QtCore import QUrl
import sys

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(750, 700)

img = QImage(960, 460, QImage.Format.Format_ARGB32)
img.fill(QColor(255, 0, 0))
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), img)

html = """
<div style="background: #F8FAFC; border: 1.5px solid #BFDBFE; padding: 12px 10px;">
  <div>Header</div>
  <img src="chart_preview.png" width="620">
  <div>Footer text</div>
</div>
"""
tb.setHtml(html)
tb.show()
tb.grab().save("scratch/test_actual_embed.png")
print("Saved scratch/test_actual_embed.png")
