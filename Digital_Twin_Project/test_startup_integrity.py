import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent

PYTHON_FILES = [
    ROOT / "services" / "patient-service" / "src" / "main.py",
    ROOT / "services" / "report-gateway" / "src" / "main.py",
    ROOT / "services" / "simulation-service" / "src" / "engine.py",
    ROOT / "services" / "xray-analysis-service" / "src" / "main.py",
    ROOT / "services" / "xray-analysis-service" / "src" / "analyzer.py",
]

TEXT_FILES = [
    ROOT / "services" / "README.md",
    ROOT / "services" / "simulation-service" / "requirements.txt",
    ROOT / "services" / "visualization-service" / "requirements.txt",
    ROOT / "services" / "xray-analysis-service" / "requirements.txt",
]

SCRIPT_FILES = [
    ROOT / "start_services_alt_ports.ps1",
    ROOT / "cleanup_legacy_gateway_ports.ps1",
]

EXTRACTED_DATA_DIR = ROOT / "extracted_data"

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


class StartupIntegrityTests(unittest.TestCase):
    def test_startup_python_files_compile_without_conflicts(self):
        for file_path in PYTHON_FILES:
            with self.subTest(file=file_path.name):
                source = file_path.read_text(encoding="utf-8")
                self.assertFalse(
                    any(marker in source for marker in CONFLICT_MARKERS),
                    f"{file_path} still contains merge conflict markers",
                )
                compile(source, str(file_path), "exec")

    def test_startup_text_files_have_no_conflict_markers(self):
        for file_path in TEXT_FILES:
            with self.subTest(file=file_path.name):
                source = file_path.read_text(encoding="utf-8")
                self.assertFalse(
                    any(marker in source for marker in CONFLICT_MARKERS),
                    f"{file_path} still contains merge conflict markers",
                )

    def test_gateway_helper_scripts_exist_and_cover_expected_ports(self):
        for file_path in SCRIPT_FILES:
            with self.subTest(file=file_path.name):
                self.assertTrue(file_path.exists(), f"{file_path} is missing")

        cleanup_script = (ROOT / "cleanup_legacy_gateway_ports.ps1").read_text(
            encoding="utf-8"
        )
        for port in ("8000", "8003", "9000"):
            with self.subTest(port=port):
                self.assertIn(port, cleanup_script)

    def test_alt_port_start_script_includes_xray_service(self):
        start_script = (ROOT / "start_services_alt_ports.ps1").read_text(encoding="utf-8")
        self.assertIn("xray-analysis-service", start_script)
        self.assertIn("9005", start_script)
        self.assertIn("XRAY_SERVICE_URL", start_script)

    def test_smoke_check_script_exists(self):
        script = ROOT / "run_multimodal_smoke_checks.py"
        self.assertTrue(script.exists(), f"{script} is missing")

    def test_cleanup_script_uses_safe_powershell_variable_interpolation(self):
        cleanup_script = (ROOT / "cleanup_legacy_gateway_ports.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("${attempt}", cleanup_script)
        self.assertIn("${procId}", cleanup_script)

    def test_extracted_data_json_files_have_no_conflict_markers(self):
        for file_path in EXTRACTED_DATA_DIR.glob("*.json"):
            with self.subTest(file=file_path.name):
                source = file_path.read_text(encoding="utf-8")
                self.assertFalse(
                    any(marker in source for marker in CONFLICT_MARKERS),
                    f"{file_path} still contains merge conflict markers",
                )


if __name__ == "__main__":
    unittest.main()
