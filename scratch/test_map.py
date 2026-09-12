import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from services.zone_map_service import generate_zone_map_image

app = QApplication(sys.argv)
# Let's see how current generate_zone_map_image behaves, but let's test with modified zoom
img = generate_zone_map_image("도마변동5구역")
img.save("scratch/test_map_current.png")
print("Saved test_map_current.png")
