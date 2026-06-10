from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_samples_exist_for_three_workflows():
    assert (ROOT / "source_data" / "10" / "倪欣然.pdf").exists()
    assert (ROOT / "source_data" / "10" / "x光" / "倪欣然17岁冠状面.PNG").exists()
