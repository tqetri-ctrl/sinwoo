import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QPainter, QTextDocument
from PyQt6.QtCore import QUrl, QRectF
from services.chart_service import render_infographic_card
from services.zone_map_service import generate_zone_map_image, get_zone_data

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(760, 1000)

zone_data = get_zone_data("도마변동5구역")
chart_img = render_infographic_card(
    title="[도마변동5구역] 2026년 최신 사업 현황 총정리!",
    zone_name="도마변동5구역",
    zone_data=zone_data
)
map_img = generate_zone_map_image("도마변동5구역")

tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), chart_img)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("zone_map_preview.png"), map_img)

# Let's test the table embed definitions
def make_table_chart_embed(desc=""):
    d = f" - {desc}" if desc else ""
    return f"""
<table class="embed-card-table" cellspacing="0" cellpadding="0" style="width: 100%; margin: 14px 0; background-color: #F8FAFC; border: 1.5px solid #BFDBFE; border-radius: 12px; border-collapse: separate;">
  <tr><td style="padding: 10px 14px 6px 14px; border: none; font-size: 13px; font-weight: bold; color: #1D4ED8; background-color: transparent;">
    📊 <strong>[핵심 요약 인포그래픽 카드]</strong>{d}
  </td></tr>
  <tr><td align="center" style="padding: 0 8px; border: none; background-color: transparent;">
    <img src="chart_preview.png" width="620" height="400" style="border-radius: 8px; border: 1px solid #CBD5E1;">
  </td></tr>
  <tr><td align="center" style="padding: 6px 14px 10px 14px; border: none; font-size: 12px; color: #64748B; background-color: transparent;">
    💡 상단 <strong>[📊 차트 복사]</strong> 버튼을 누르면 이 고화질 카드가 클립보드에 복사되어 블로그에 바로 첨부됩니다.
  </td></tr>
</table>
"""

def make_table_map_embed(desc=""):
    d = f" - {desc}" if desc else ""
    return f"""
<table class="embed-card-table" cellspacing="0" cellpadding="0" style="width: 100%; margin: 14px 0; background-color: #F0F9FF; border: 1.5px solid #BAE6FD; border-radius: 12px; border-collapse: separate;">
  <tr><td style="padding: 10px 14px 6px 14px; border: none; font-size: 13px; font-weight: bold; color: #0284C7; background-color: transparent;">
    🗺️ <strong>[정비구역 / 매물 위치도]</strong>{d}
  </td></tr>
  <tr><td align="center" style="padding: 0 8px; border: none; background-color: transparent;">
    <img src="zone_map_preview.png" width="620" height="400" style="border-radius: 8px; border: 1px solid #CBD5E1;">
  </td></tr>
  <tr><td align="center" style="padding: 6px 14px 10px 14px; border: none; font-size: 12px; color: #64748B; background-color: transparent;">
    💡 상단 <strong>[🗺️ 구역 지도 복사]</strong> 버튼을 누르면 이 고화질 위치도가 클립보드에 복사되어 블로그에 바로 첨부됩니다.
  </td></tr>
</table>
"""

sample_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif;
    background-color: #FFFFFF;
    color: #222222;
    padding: 24px 20px;
    margin: 0;
    font-size: 15px;
}}
.blog-container {{ max-width: 680px; margin: 0 auto; }}
.blog-header {{ border-bottom: 2px solid #03C75A; padding-bottom: 16px; margin-bottom: 24px; }}
.blog-category {{ font-size: 13px; font-weight: 700; color: #03C75A; margin-bottom: 6px; }}
.blog-title {{ font-size: 24px; font-weight: 800; color: #111111; margin: 0; }}
.blog-content p {{ margin-bottom: 18px; line-height: 1.8; }}
.blog-content h3 {{ font-size: 18px; border-left: 4px solid #03C75A; padding-left: 10px; margin-top: 28px; margin-bottom: 14px; }}
table.embed-card-table td {{ border: none !important; }}
</style>
</head>
<body>
<div class="blog-container">
  <div class="blog-header">
    <div class="blog-category">부동산 소식 & 매물 브리핑</div>
    <h1 class="blog-title">[도마변동5구역] 2026년 최신 현황 총정리! 사업시행인가 이후 관리처분계획</h1>
  </div>
  <div class="blog-content">
    <p>안녕하세요! 신우 공인중개사사무소입니다. 대전 서구 핵심 재개발 사업지인 <strong>도마·변동 5구역</strong>의 2026년 최신 사업 현황을 총정리해 드립니다.</p>
    {make_table_chart_embed("도마변동 5구역 핵심 사업 요약표")}
    <h3>1. 사업 개요 및 추진 단계 로드맵</h3>
    <p>도마변동 5구역은 총 2,870여 세대 규모로 건설되는 대단지 프리미엄 신축 아파트 단지입니다.</p>
    {make_table_map_embed("대전 서구 도마동 80-37 및 도마변동5구역 경계 구역 지도")}
    <h3>2. 입지 프리미엄 분석</h3>
    <p>유등천 수변 공원과 트램 2호선 등의 교통 호재를 모두 누리는 최상의 입지 조건입니다.</p>
  </div>
</div>
</body>
</html>
"""

tb.setHtml(sample_html)
doc = tb.document()
doc.setTextWidth(720)

total_h = int(doc.size().height()) + 40
full_img = QImage(740, total_h, QImage.Format.Format_ARGB32)
full_img.fill(0xFFFFFFFF)

p = QPainter(full_img)
doc.drawContents(p, QRectF(10, 10, 720, total_h))
p.end()

full_img.save("scratch/test_perfect_full_render.png")
print("Saved scratch/test_perfect_full_render.png, total height:", total_h)
