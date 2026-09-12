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

# Try removing <style> tags
no_style = full_html[:full_html.find("<style>")] + full_html[full_html.find("</style>")+8:]
tb.setHtml(no_style)
tb.document().setTextWidth(720)
b2 = tb.document().findBlockByNumber(2)
b3 = tb.document().findBlockByNumber(3)
pos2 = b2.layout().position().y() if b2 and b2.layout() else -1
pos3 = b3.layout().position().y() if b3 and b3.layout() else -1
print("Without <style>: b2 y=", pos2, "b3 y=", pos3)

# Now check CSS rules one by one
import re
css_match = re.search(r'<style>(.*?)</style>', full_html, re.DOTALL)
css_content = css_match.group(1) if css_match else ""

# Remove line-height from body
test_css = css_content.replace("line-height: 1.85;", "")
test_html = full_html.replace(css_content, test_css)
tb.setHtml(test_html)
tb.document().setTextWidth(720)
b2 = tb.document().findBlockByNumber(2)
b3 = tb.document().findBlockByNumber(3)
print("Without line-height: b2 y=", b2.layout().position().y(), "b3 y=", b3.layout().position().y())
