from pathlib import Path
from typing import List, Dict, Optional
import pydicom
from PIL import Image
import numpy as np
from tqdm import tqdm

from src.core.config_manager import ConfigManager
from src.utils.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)


class DicomScanner:
    """Scan directories for DICOM files"""

    @staticmethod
    def scan_directory(directory: Path, recursive: bool = True) -> List[Path]:
        """
        Scan directory for DICOM files

        Args:
            directory: Path to scan
            recursive: Scan subdirectories

        Returns:
            List of DICOM file paths
        """
        logger.info(f"Scanning directory: {directory}")

        pattern = "**/*.dcm" if recursive else "*.dcm"
        dcm_files = list(directory.glob(pattern))

        logger.info(f"Found {len(dcm_files)} DICOM files")
        return sorted(dcm_files)

    @staticmethod
    def validate_dicom(file_path: Path) -> bool:
        """Validate if file is a valid DICOM"""
        try:
            pydicom.dcmread(file_path, stop_before_pixels=True)
            return True
        except Exception as e:
            logger.warning(f"Invalid DICOM file {file_path}: {e}")
            return False


class DicomConverter:
    """Convert DICOM files to JPG"""

    def __init__(self, target_resolution: tuple = (1024, 768), quality: int = 95):
        self.target_resolution = target_resolution
        self.quality = quality

    def convert_to_jpg(self, dcm_path: Path, output_path: Optional[Path] = None) -> Image.Image:
        """
        Convert DICOM to JPG

        Args:
            dcm_path: Path to DICOM file
            output_path: Optional output path for JPG

        Returns:
            PIL Image object
        """
        try:
            # Read DICOM
            dcm = pydicom.dcmread(dcm_path)

            # Get pixel array
            pixel_array = dcm.pixel_array

            # Handle photometric interpretation
            image = self._apply_photometric_interpretation(pixel_array, dcm)

            # Convert to PIL Image
            pil_image = Image.fromarray(image)

            # Resize if needed
            if pil_image.size != self.target_resolution:
                pil_image = pil_image.resize(self.target_resolution, Image.Resampling.LANCZOS)

            # Save if output path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                pil_image.save(output_path, 'JPEG', quality=self.quality)
                logger.debug(f"Saved JPG: {output_path}")

            return pil_image

        except Exception as e:
            logger.error(f"Error converting {dcm_path}: {e}")
            raise

    def _apply_photometric_interpretation(self, pixel_array: np.ndarray, dcm) -> np.ndarray:
        """Apply photometric interpretation for correct colors"""

        # Normalize to 8-bit
        if pixel_array.dtype != np.uint8:
            pixel_array = self._normalize_to_uint8(pixel_array)

        # Handle different photometric interpretations
        photometric = getattr(dcm, 'PhotometricInterpretation', 'MONOCHROME2')

        if photometric == 'MONOCHROME1':
            # Invert for MONOCHROME1
            pixel_array = 255 - pixel_array

        # Convert to RGB if grayscale
        if len(pixel_array.shape) == 2:
            pixel_array = np.stack([pixel_array] * 3, axis=-1)

        return pixel_array

    @staticmethod
    def _normalize_to_uint8(array: np.ndarray) -> np.ndarray:
        """Normalize array to uint8 range"""
        array = array.astype(float)
        array_min = array.min()
        array_max = array.max()

        if array_max > array_min:
            array = (array - array_min) / (array_max - array_min) * 255

        return array.astype(np.uint8)

    def get_metadata(self, dcm_path: Path) -> Dict:
        """Extract useful metadata from DICOM"""
        try:
            dcm = pydicom.dcmread(dcm_path, stop_before_pixels=True)

            return {
                'patient_id': getattr(dcm, 'PatientID', 'Unknown'),
                'study_date': getattr(dcm, 'StudyDate', 'Unknown'),
                'modality': getattr(dcm, 'Modality', 'Unknown'),
                'body_part': getattr(dcm, 'BodyPartExamined', 'Unknown'),
                'institution': getattr(dcm, 'InstitutionName', 'Unknown'),
            }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}


class DicomProcessor:
    """Main DICOM processing orchestrator"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.scanner = DicomScanner()
        self.converter = DicomConverter(
            target_resolution=config.dicom.target_resolution,
            quality=config.dicom.output_quality
        )

    def process_directory(self, directory: Path, output_dir: Path) -> List[Path]:
        """
        Process all DICOM files in directory

        Args:
            directory: Input directory with DICOM files
            output_dir: Output directory for JPG files

        Returns:
            List of processed JPG file paths
        """
        # Scan for DICOM files
        dcm_files = self.scanner.scan_directory(directory)

        if not dcm_files:
            logger.warning("No DICOM files found")
            return []

        # Process each file
        jpg_paths = []
        for dcm_file in tqdm(dcm_files, desc="Converting DICOMs"):
            try:
                # Create output path
                relative_path = dcm_file.relative_to(directory)
                output_path = output_dir / relative_path.with_suffix('.jpg')

                # Convert
                self.converter.convert_to_jpg(dcm_file, output_path)
                jpg_paths.append(output_path)

            except Exception as e:
                logger.error(f"Failed to process {dcm_file}: {e}")
                continue

        logger.info(f"Successfully converted {len(jpg_paths)}/{len(dcm_files)} files")
        return jpg_paths