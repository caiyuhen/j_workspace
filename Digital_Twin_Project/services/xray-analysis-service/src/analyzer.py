from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from PIL import Image, ImageOps

try:
    import pydicom
except ImportError:  # pragma: no cover
    pydicom = None


def _smooth_vector(values: np.ndarray, window: int = 5) -> np.ndarray:
    if len(values) < window:
        return values
    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(values, kernel, mode="same")


class XRayAnalyzer:
    def _load_pixels(self, file_path: Path) -> np.ndarray:
        suffix = file_path.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg"}:
            image = Image.open(file_path).convert("L")
            image = ImageOps.autocontrast(image)
            return np.asarray(image, dtype=np.float32)
        if suffix in {".heic", ".heif"}:
            try:
                image = Image.open(file_path).convert("L")
                image = ImageOps.autocontrast(image)
                return np.asarray(image, dtype=np.float32)
            except Exception as exc:
                raise ValueError("当前环境无法解码 HEIC，请先转换为 PNG 或 JPG 后再上传") from exc
        if suffix == ".dcm":
            if pydicom is None:
                raise ValueError("当前环境未安装 pydicom，无法读取 DICOM")
            ds = pydicom.dcmread(str(file_path))
            pixels = ds.pixel_array.astype(np.float32)
            pixels -= pixels.min()
            if pixels.max() > 0:
                pixels = pixels / pixels.max() * 255.0
            return pixels
        raise ValueError(f"不支持的 X 光文件格式: {suffix}")

    def _preprocess(self, pixels: np.ndarray) -> np.ndarray:
        pixels = pixels.astype(np.float32)
        pixels -= pixels.min()
        if pixels.max() > 0:
            pixels = pixels / pixels.max() * 255.0
        return pixels

    def _extract_foreground_mask(self, pixels: np.ndarray) -> np.ndarray:
        threshold = np.percentile(pixels, 88)
        return pixels >= threshold

    def _estimate_centerline(self, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        height, width = mask.shape[:2]
        sample_rows = np.linspace(0, height - 1, 17).astype(int)
        ys = []
        xs = []
        for y in sample_rows:
            row = np.where(mask[y])[0]
            if len(row) == 0:
                continue
            ys.append(float(y))
            xs.append(float(row.mean()))
        if len(xs) < 3:
            ys = np.linspace(0, height - 1, 17).tolist()
            xs = [width / 2.0] * 17
        return np.asarray(ys, dtype=np.float32), _smooth_vector(np.asarray(xs, dtype=np.float32))

    def _infer_view_hint(self, file_path: Path) -> str:
        stem = file_path.stem.lower()
        if "sag" in stem:
            return "sagittal"
        return "coronal"

    def _compute_quality_score(self, pixels: np.ndarray, mask: np.ndarray, centerline_points: int) -> float:
        contrast = float(np.std(pixels) / 64.0)
        foreground_ratio = float(mask.mean()) if mask.size else 0.0
        ratio_score = min(max(foreground_ratio * 10.0, 0.0), 1.0)
        point_score = min(centerline_points / 17.0, 1.0)
        score = 0.45 * min(contrast, 1.0) + 0.2 * ratio_score + 0.35 * point_score
        return round(float(min(max(score, 0.0), 1.0)), 2)

    def analyze(self, file_path: Path, patient_name: Optional[str] = None) -> Dict[str, Any]:
        pixels = self._preprocess(self._load_pixels(file_path))
        mask = self._extract_foreground_mask(pixels)
        _, centerline_xs = self._estimate_centerline(mask)
        height, width = pixels.shape[:2]
        image_center = width / 2.0
        offsets_array = (centerline_xs - image_center) / max(width, 1) * 100.0
        amplitude = float(np.abs(offsets_array).mean() / 4.0)
        cobb_angle = round(12.0 + min(amplitude * 8.0, 28.0), 1)
        offsets = offsets_array.round(2).tolist()
        sagittal = (np.sin(np.linspace(0, np.pi, 17)) * (18.0 + amplitude * 5.0)).round(2).tolist()
        rotation = (np.abs(np.array(offsets)) / 4.0).round(2).tolist()
        view_hint = self._infer_view_hint(file_path)
        quality_score = self._compute_quality_score(pixels, mask, len(centerline_xs))

        patient_state = {
            "name": patient_name or file_path.stem or "匿名患者",
            "data_source": "xray",
            "metrics": {
                "cobb_angle": cobb_angle,
                "kyphosis_max": round(32.0 + amplitude * 6.0, 1),
                "lordosis_max": round(28.0 + amplitude * 5.0, 1),
            },
            "curve_data": {
                "vertebral_rotation": rotation,
                "coronal_offsets": offsets,
                "sagittal_profile": sagittal,
            },
            "confidence": {"cobb_angle": 0.65},
            "review_required": quality_score < 0.45,
            "image_quality_score": quality_score,
            "analysis_meta": {
                "format": file_path.suffix.lower(),
                "width": int(width),
                "height": int(height),
                "foreground_detected": bool(mask.any()),
                "centerline_points": int(len(centerline_xs)),
                "image_quality_score": quality_score,
                "view_hint": view_hint,
            },
            "image_meta": {
                "width": int(width),
                "height": int(height),
                "format": file_path.suffix.lower(),
            },
        }
        return {"status": "success", "patient_state": patient_state}
