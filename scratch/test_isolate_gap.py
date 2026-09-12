import sys
sys.path.insert(0, '.')
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QTextDocument
from PyQt6.QtCore import QUrl

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(720, 800)

img = QImage(620, 400, QImage.Format.Format_ARGB32)
img.fill(0xFF1E3A8A)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl('chart_preview.png'), img)

# Test 1: Just img inside div
html_test1 = """
<div style="background: #F8FAFC; border: 1.5px solid #BFDBFE; padding: 10px;">
  <div>Header</div>
  <img src="chart_preview.png" width="620" height="400">
  <div>Footer</div>
</div>
"""
tb.setHtml(html_test1)
tb.document().setTextWidth(720)
b_hdr = tb.document().findBlockByNumber(0)
b_ftr = tb.document().findBlockByNumber(1)
print("Test 1 pos:", b_hdr.layout().position() if b_hdr.layout() else None,
      b_ftr.layout().position() if b_ftr.layout() else None)

# Test 2: With outer css styles
from ui.styles import generate_blog_preview_html
html_test2 = generate_blog_preview_html('Title', '[추천 차트: 도마변동 5구역]', [], True, False)
tb.setHtml(html_test2)
tb.document().setTextWidth(720)
for b in range(tb.document().blockCount()):
    blk = tb.document().findBlockByNumber(b)
    l = blk.layout()
    pos_y = l.position().y() if l else -1
    h = l.boundingRect().height() if l else -1
    print(f"Test 2 Block {b}: y={pos_y:.1f}, h={h:.1f}")
