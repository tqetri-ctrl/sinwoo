from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QColor, QTextDocument
from PyQt6.QtCore import QUrl
import sys

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(750, 700)

# Create image at native width 680, height 400
w, h = 680, 400
img = QImage(w, h, QImage.Format.Format_ARGB32)
img.fill(QColor(37, 99, 235))
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), img)

html = f"""
<div style="background: #F8FAFC; border: 1.5px solid #BFDBFE; border-radius: 12px; padding: 12px; text-align: center;">
  <div style="font-size: 13px; font-weight: bold; color: #1D4ED8; margin-bottom: 8px; text-align: left;">
    📊 <strong>[핵심 요약 인포그래픽 카드]</strong>
  </div>
  <img src="chart_preview.png" width="{w}" height="{h}" style="border-radius: 8px; display: block; margin: 0 auto;">
  <div style="font-size: 12px; color: #64748B; margin-top: 8px;">
    💡 상단 <strong>[📊 차트 복사]</strong> 버튼을 누르면 이 고화질 카드가 클립보드에 복사되어 블로그에 바로 첨부됩니다.
  </div>
</div>
"""
tb.setHtml(html)
tb.show()
tb.grab().save("scratch/test_exact_size.png")
print("Saved scratch/test_exact_size.png")
