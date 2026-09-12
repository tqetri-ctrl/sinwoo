from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QTextDocument
from PyQt6.QtCore import QUrl
import sys

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(600, 500)
img = QImage(600, 380, QImage.Format.Format_ARGB32)
img.fill(100)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("im.png"), img)
tb.setHtml('<div style="padding: 10px;"><img src="im.png" width="100%"></div>')
tb.show()
print("Width 100% test:", tb.document().toHtml()[:100])
tb.grab().save("scratch/test_w100.png")
