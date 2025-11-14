from PIL import Image, ImageDraw
import pytesseract
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from src.core.config_manager import ConfigManager
from src.utils.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)

@dataclass
class BoundingBox:
    """Text region bounding box"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    text: str

class CropRemover:
    """Simple crop-based PHI removal"""

    def __init__(self, crop_percentage: float = 0.07):
        self.crop_percentage = crop_percentage

    def remove_phi(self, image: Image.Image) -> Image.Image:
        """Remove PHI by cropping top percentage"""
        width, height = image.size

        # Calculate pixels to crop based on percentage
        crop_pixels = int(height * self.crop_percentage)

        # Crop from (0, crop_pixels) to (width, height)
        cropped = image.crop((0, crop_pixels, width, height))

        logger.debug(f"Cropped {crop_pixels} pixels ({self.crop_percentage*100:.1f}%) from top")
        return cropped


class OcrRemover:
    """OCR-based PHI detection and removal"""

    def __init__(self, languages: List[str] = ['eng'], confidence_threshold: float = 0.6):
        self.languages = '+'.join(languages)
        self.confidence_threshold = confidence_threshold

        # Verify Tesseract installation
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError("Tesseract OCR not installed")

    def detect_text_regions(self, image: Image.Image, top_only: bool = True) -> List[BoundingBox]:
        """
        Detect text regions in image

        Args:
            image: PIL Image
            top_only: Only detect in top portion (first 100 pixels)

        Returns:
            List of bounding boxes with detected text
        """
        # If top_only, crop for detection
        if top_only:
            width, height = image.size
            detection_image = image.crop((0, 0, width, min(100, height)))
        else:
            detection_image = image

        # Run OCR with bounding box data
        try:
            data = pytesseract.image_to_data(
                detection_image,
                lang=self.languages,
                output_type=pytesseract.Output.DICT
            )

            boxes = []
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                confidence = float(data['conf'][i])
                text = data['text'][i].strip()

                # Filter by confidence and non-empty text
                if confidence >= self.confidence_threshold * 100 and text:
                    box = BoundingBox(
                        x=data['left'][i],
                        y=data['top'][i],
                        width=data['width'][i],
                        height=data['height'][i],
                        confidence=confidence / 100,
                        text=text
                    )
                    boxes.append(box)

            logger.debug(f"Detected {len(boxes)} text regions")
            return boxes

        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return []

    def redact_regions(self, image: Image.Image, regions: List[BoundingBox]) -> Image.Image:
        """Redact detected text regions with black boxes"""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)

        for box in regions:
            # Add small padding
            padding = 2
            x1 = max(0, box.x - padding)
            y1 = max(0, box.y - padding)
            x2 = min(image.width, box.x + box.width + padding)
            y2 = min(image.height, box.y + box.height + padding)

            # Draw black rectangle
            draw.rectangle([x1, y1, x2, y2], fill='black')

            logger.debug(f"Redacted text: '{box.text}' at ({x1},{y1})")

        return img_copy

    def remove_phi(self, image: Image.Image) -> Image.Image:
        """Remove PHI using OCR detection"""
        regions = self.detect_text_regions(image, top_only=True)

        if regions:
            return self.redact_regions(image, regions)
        else:
            logger.warning("No text detected, returning original image")
            return image


class HybridRemover:
    """Hybrid approach: OCR + fallback crop"""

    def __init__(self, crop_percentage: float = 0.07, ocr_languages: List[str] = ['eng']):
        self.crop_remover = CropRemover(crop_percentage)
        self.ocr_remover = OcrRemover(languages=ocr_languages)

    def remove_phi(self, image: Image.Image) -> Image.Image:
        """
        Try OCR first, fallback to crop if OCR fails or finds minimal text
        """
        try:
            # Try OCR detection
            regions = self.ocr_remover.detect_text_regions(image, top_only=True)

            # If OCR found significant text, redact it
            if len(regions) >= 3:  # Arbitrary threshold
                logger.info("Using OCR-based PHI removal")
                return self.ocr_remover.redact_regions(image, regions)
            else:
                # Fallback to crop
                logger.info("Falling back to crop-based PHI removal")
                return self.crop_remover.remove_phi(image)

        except Exception as e:
            logger.warning(f"OCR failed, using crop: {e}")
            return self.crop_remover.remove_phi(image)


class PhiRemover:
    """Main PHI removal orchestrator"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.method = config.phi_removal.method

        # Initialize appropriate remover
        if self.method == 'crop':
            self.remover = CropRemover(config.phi_removal.crop_percentage)
        elif self.method == 'ocr':
            self.remover = OcrRemover(
                languages=config.phi_removal.ocr_languages,
                confidence_threshold=config.phi_removal.text_detection_confidence
            )
        elif self.method == 'hybrid':
            self.remover = HybridRemover(
                crop_percentage=config.phi_removal.crop_percentage,
                ocr_languages=config.phi_removal.ocr_languages
            )
        else:
            raise ValueError(f"Unknown PHI removal method: {self.method}")

    def remove_phi(self, image: Image.Image) -> Image.Image:
        """Remove PHI from image"""
        logger.info(f"Removing PHI using method: {self.method}")
        return self.remover.remove_phi(image)

    def process_file(self, input_path: str, output_path: str):
        """Process single image file"""
        image = Image.open(input_path)
        cleaned = self.remove_phi(image)
        cleaned.save(output_path, 'JPEG', quality=95)
        logger.info(f"Saved PHI-removed image: {output_path}")