import sys
sys.path.insert(0, ".")
from ui.styles import generate_blog_preview_html

sample_body = """
[추천 차트: 도마변동 5구역 핵심 사업 요약표]
"""
html = generate_blog_preview_html("Title", sample_body, [], True, True)
with open("scratch/dumped_preview.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Dumped html")
