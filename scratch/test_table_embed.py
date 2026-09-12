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

# Table layout test
table_html = """
<style>
body { font-family: 'Malgun Gothic'; margin: 0; padding: 20px; background: white; }
</style>
<body>
<p>Hello world paragraph</p>
<table style="width: 100%; margin: 12px 0; background-color: #F8FAFC; border: 1.5px solid #BFDBFE; border-radius: 12px;" cellspacing="0" cellpadding="0">
  <tr><td style="padding: 10px 12px 6px 12px; border: none; font-size: 13px; font-weight: bold; color: #1D4ED8; background-color: transparent;">
    📊 <strong>[핵심 요약 인포그래픽 카드]</strong> - 도마변동 5구역 핵심 사업 요약표
  </td></tr>
  <tr><td align="center" style="padding: 2px 10px; border: none; background-color: transparent;">
    <img src="chart_preview.png" width="620" height="400">
  </td></tr>
  <tr><td align="center" style="padding: 6px 12px 10px 12px; border: none; font-size: 12px; color: #64748B; background-color: transparent;">
    💡 상단 <strong>[📊 차트 복사]</strong> 버튼을 누르면 이 고화질 카드가 클립보드에 복사되어 블로그에 바로 첨부됩니다.
  </td></tr>
</table>
<p>After table paragraph</p>
</body>
"""

tb.setHtml(table_html)
tb.show()
tb.grab().save("scratch/test_table_embed.png")
print("Saved scratch/test_table_embed.png")
