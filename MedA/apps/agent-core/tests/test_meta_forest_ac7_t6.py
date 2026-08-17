import pytest
import re
from xml.etree import ElementTree as ET


dummy_k5_studies = [
    {"label": "Smith 2010", "effect": 1.23, "ci_low": 0.89, "ci_high": 1.70, "weight": 30.0},
    {"label": "Jones 2011", "effect": 0.91, "ci_low": 0.61, "ci_high": 1.36, "weight": 25.0},
    {"label": "Lee 2012", "effect": 1.55, "ci_low": 1.10, "ci_high": 2.18, "weight": 20.0},
    {"label": "Wang 2013", "effect": 1.02, "ci_low": 0.72, "ci_high": 1.45, "weight": 15.0},
    {"label": "Brown 2014", "effect": 1.40, "ci_low": 0.98, "ci_high": 2.00, "weight": 10.0},
]

dummy_pooled = {"effect": 1.18, "ci_low": 1.01, "ci_high": 1.37}

dummy_I2_67pct = {"I2_pct": 67.2, "tau2": 0.0234}


@pytest.fixture
def svg_bytes():
    from app.services.meta_forest import forest_svg_bytes
    return forest_svg_bytes(dummy_k5_studies, dummy_pooled, dummy_I2_67pct)


class TestAC7T6:
    def test_T6A1_svg_header_and_viewbox(self, svg_bytes):
        assert isinstance(svg_bytes, bytes)
        assert svg_bytes.startswith(b"<svg")
        decoded = svg_bytes.decode("utf-8")
        assert 'viewBox="' in decoded
        m = re.search(r'viewBox="([^"]+)"', decoded)
        assert m is not None
        assert len(m.group(1).strip()) > 0

    def test_T6A2_diamond_polygon_points(self, svg_bytes):
        decoded = svg_bytes.decode("utf-8")
        root = ET.fromstring(decoded)
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        diamond = root.find(f".//{ns}polygon[@id='diamond-pooled']")
        assert diamond is not None, "<polygon id='diamond-pooled' not found"
        points_attr = diamond.get("points")
        assert points_attr is not None and len(points_attr.strip()) > 0
        pairs = points_attr.strip().split()
        assert len(pairs) == 4, f"Expected 4 coordinate pairs, got {len(pairs)}: {pairs}"
        for pair in pairs:
            xy = pair.split(",")
            assert len(xy) == 2, f"Pair {pair} should have x,y"
            float(xy[0])
            float(xy[1])

    def test_T6A3_no_external_script(self, svg_bytes):
        decoded = svg_bytes.decode("utf-8")
        count = len(re.findall(r"<script", decoded, flags=re.IGNORECASE))
        assert count == 0, f"Found {count} <script> tags"

    def test_T6A4_svg_size_under_150kb(self, svg_bytes):
        assert len(svg_bytes) <= 150 * 1024, f"SVG too large: {len(svg_bytes)} bytes"

    def test_T6A5_contains_i2_text(self, svg_bytes):
        decoded = svg_bytes.decode("utf-8")
        pattern = r"I²\s*=\s*\d+(\.\d+)?%?"
        m = re.search(pattern, decoded)
        assert m is not None, f"I² text pattern not found in SVG content"
