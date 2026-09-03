import base64
import io
import logging
from pathlib import Path
from typing import Tuple, Union, Optional
from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger("multimodal.image_processing")

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logger.warning("OpenCV not installed. Falling back to PIL-based image processing.")


class ImageProcessor:
    """Image enhancement, deskewing, and formatting utilities for OCR and Vision models."""

    @staticmethod
    def load_image(image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """Load an image from filepath, bytes, or return PIL Image."""
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        if isinstance(image_input, (str, Path)):
            return Image.open(str(image_input)).convert("RGB")
        if isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert("RGB")
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    @staticmethod
    def to_base64(image_input: Union[str, Path, bytes, Image.Image], format: str = "PNG") -> str:
        """Convert an image to a base64-encoded string (for Ollama/vLLM vision APIs)."""
        if isinstance(image_input, (str, Path)):
            with open(str(image_input), "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        if isinstance(image_input, bytes):
            return base64.b64encode(image_input).decode("utf-8")
        if isinstance(image_input, Image.Image):
            buffered = io.BytesIO()
            image_input.save(buffered, format=format)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        raise ValueError("Invalid image input for base64 encoding")

    @classmethod
    def preprocess_for_ocr(cls, image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """
        Enhance image contrast, deskew orientation, and remove noise to optimize OCR accuracy.
        """
        pil_img = cls.load_image(image_input)
        if not HAS_OPENCV:
            # Fallback to PIL enhancement
            gray = ImageOps.grayscale(pil_img)
            enhancer = ImageEnhance.Contrast(gray)
            return enhancer.enhance(1.8)

        # OpenCV pipeline
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # 1. Grayscale
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # 2. Deskew
        gray, angle = cls._deskew(gray)

        # 3. Contrast enhancement via CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 4. Light denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Return enhanced PIL Image
        return Image.fromarray(denoised)

    @classmethod
    def binarize_for_text(cls, image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """Otsu thresholding for sharp text isolation."""
        pil_img = cls.load_image(image_input)
        if not HAS_OPENCV:
            gray = ImageOps.grayscale(pil_img)
            return gray.point(lambda p: 255 if p > 128 else 0, '1')

        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)

    @staticmethod
    def _deskew(gray_img: "np.ndarray") -> Tuple["np.ndarray", float]:
        """Detect skew angle and rotate image to straighten text."""
        try:
            # Invert colors: text white, background black
            thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Find coordinates of all foreground pixels
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 50:
                return gray_img, 0.0

            angle = cv2.minAreaRect(coords)[-1]
            # Handle OpenCV angle conventions
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Only rotate if significant skew detected (between 0.5 and 45 degrees)
            if abs(angle) < 0.5 or abs(angle) > 45:
                return gray_img, 0.0

            (h, w) = gray_img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                gray_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            return rotated, angle
        except Exception as e:
            logger.debug(f"Deskew skipped: {e}")
            return gray_img, 0.0
