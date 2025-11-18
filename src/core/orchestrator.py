from pathlib import Path
from typing import List, Optional, Tuple
import os
import time
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.utils.logger import LoggerManager
from src.processors.dicom_processor import DicomProcessor
from src.processors.phi_remover import PhiRemover
from src.templates.template_manager import TemplateManager, TemplateSelector
from src.generators.report_generator import ReportGenerator

logger = LoggerManager.get_logger(__name__)


class CaseOrchestrator:
    """
    Main orchestrator for processing complete ultrasound patient cases.

    Coordinates all components to process a patient case from DICOM files
    to final report generation.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the CaseOrchestrator with all necessary components.

        Args:
            config_path: Path to configuration file
        """
        # Initialize configuration
        self.config = ConfigManager(config_path)
        self.config.ensure_directories()

        # Initialize logger
        self.logger = LoggerManager(
            log_dir=self.config.paths.logs_dir,
            level=getattr(self.config.logging, 'level', 'INFO') if hasattr(self.config, 'logging') else 'INFO'
        )

        # Initialize components
        self.dicom_processor = DicomProcessor(self.config)
        self.phi_remover = PhiRemover(self.config)
        self.template_manager = TemplateManager(str(self.config.paths.templates_json))
        self.template_selector = TemplateSelector(self.template_manager)
        self.report_generator = ReportGenerator(self.config)

        logger.info("CaseOrchestrator initialized with all components")

    def _get_output_dirs(self, input_dir: Path) -> tuple[Path, Path, Path]:
        """
        Get output directories for the case processing.

        Args:
            input_dir: Input directory containing DICOM files

        Returns:
            Tuple of (temp_images_dir, cleaned_images_dir, reports_dir)
        """
        case_name = input_dir.name

        # Create timestamped subdirectories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_output_dir = self.config.paths.temp_output_dir / f"{case_name}_{timestamp}"

        temp_images_dir = case_output_dir / "temp_images"
        cleaned_images_dir = case_output_dir / "cleaned_images"
        reports_dir = Path(self.config.paths.outputs_dir)

        # Ensure directories exist
        temp_images_dir.mkdir(parents=True, exist_ok=True)
        cleaned_images_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)

        return temp_images_dir, cleaned_images_dir, reports_dir

    def _select_template(self, input_dir: Path) -> Optional[object]:
        """
        Select appropriate template based on input directory name.

        Args:
            input_dir: Input directory path

        Returns:
            Selected Template object or None
        """
        logger.info(f"[NEW CODE v2] _select_template called with input_dir: {input_dir}")
        
        # Find the first subdirectory within input_dir for template selection
        # This ensures we use the body region folder name, not the patient name
        subdirs = [d for d in input_dir.iterdir() if d.is_dir()]
        
        logger.info(f"[NEW CODE v2] Found {len(subdirs)} subdirectories in {input_dir}")
        
        if subdirs:
            # Use the first subdirectory's name (body region folder)
            template_selection_name = subdirs[0].name
            logger.info(f"[NEW CODE v2] Using subdirectory name for template selection: {template_selection_name}")
        else:
            # Fallback to input_dir name if no subdirectories found
            template_selection_name = input_dir.name
            logger.info(f"[NEW CODE v2] No subdirectories found, using input_dir name: {template_selection_name}")
        
        # Extract directory names for template selection
        dir_names = [template_selection_name]

        logger.info(f"[NEW CODE v2] Selecting template based on directory names: {dir_names}")

        template, info = self.template_selector.select_template_with_info(dir_names)

        if template:
            logger.info(f"Selected template: {template.name}")
        else:
            logger.warning("No template selected, will use default")

        return template

    def _generate_report_filename(self, input_dir: Path) -> str:
        """
        Generate filename for the final report.

        Args:
            input_dir: Input directory path

        Returns:
            Report filename
        """
        case_name = input_dir.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Extract patient info if available from directory name
        patient_id = "Unknown"
        if "_" in case_name:
            parts = case_name.split("_")
            if len(parts) >= 2:
                patient_id = parts[-1]  # Assume last part is patient identifier

        filename = f"Report_{patient_id}_{timestamp}.txt"
        return filename

    def process_case(self, input_dir: str) -> Tuple[str, str, float]:
        """
        Process a complete patient case from DICOM files to final report.

        Args:
            input_dir: Path to directory containing DICOM files

        Returns:
            Tuple of (report_path, patient_name, duration)
            - report_path: Path to the generated report file
            - patient_name: Name/identifier of the patient
            - duration: Processing time in seconds

        Raises:
            Exception: If any step in the processing fails
        """
        logger.info("[NEW CODE v2] process_case called - Returns Tuple[str, str, float]")
        
        # Record start time
        start_time = time.time()
        
        input_path = Path(input_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        logger.info(f"[NEW CODE v2] Starting case processing for: {input_path}")

        try:
            # Step 1: Get output directories
            temp_images_dir, cleaned_images_dir, reports_dir = self._get_output_dirs(input_path)
            logger.info(f"Output directories: temp={temp_images_dir}, cleaned={cleaned_images_dir}, reports={reports_dir}")

            # Step 2: Process DICOM files to JPGs
            logger.info("Step 1: Converting DICOM files to JPG")
            temp_image_paths = self.dicom_processor.process_directory(input_path, temp_images_dir)

            if not temp_image_paths:
                raise ValueError("No DICOM files were successfully converted to images")

            logger.info(f"Converted {len(temp_image_paths)} DICOM files to JPG")

            # Step 3: Remove PHI from images
            logger.info("Step 2: Removing PHI from images")
            cleaned_image_paths = []

            for temp_image_path in temp_image_paths:
                try:
                    # Create corresponding cleaned path
                    relative_path = temp_image_path.relative_to(temp_images_dir)
                    cleaned_path = cleaned_images_dir / relative_path

                    # Load image and remove PHI
                    from PIL import Image
                    image = Image.open(temp_image_path)
                    cleaned_image = self.phi_remover.remove_phi(image)

                    # Save cleaned image
                    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
                    cleaned_image.save(cleaned_path, 'JPEG', quality=95)

                    cleaned_image_paths.append(str(cleaned_path))
                    logger.debug(f"PHI removed from: {cleaned_path}")

                except Exception as e:
                    logger.error(f"Failed to process image {temp_image_path}: {e}")
                    continue

            if not cleaned_image_paths:
                raise ValueError("No images were successfully cleaned of PHI")

            logger.info(f"Successfully cleaned {len(cleaned_image_paths)} images")

            # Step 4: Select report template
            logger.info("Step 3: Selecting report template")
            template = self._select_template(input_path)

            if not template:
                # Use default template
                try:
                    template = self.template_manager.get_template_by_name("ULTRASOUND OF BOTH BREASTS")
                    logger.warning("Using default template: ULTRASOUND OF BOTH BREASTS")
                except KeyError:
                    raise ValueError("No suitable template found and default template unavailable")

            # Step 5: Generate report
            logger.info("Step 4: Generating report using LLM")
            report_text = self.report_generator.generate_report(cleaned_image_paths, template, template.name)

            # Post-processing: Remove markdown formatting
            report_text = report_text.replace('**', '')
            logger.debug("Removed markdown bolding from report")

            # Step 6: Save report
            report_filename = self._generate_report_filename(input_path)
            report_path = reports_dir / report_filename

            self.report_generator.save_report(report_text, report_path)

            # Calculate processing duration
            duration = time.time() - start_time

            logger.info(f"[NEW CODE v2] Case processing completed successfully in {duration:.2f} seconds. Report saved to: {report_path}")

            # Extract patient name
            patient_name = input_path.name

            logger.info(f"[NEW CODE v2] Returning tuple: (report_path={report_path}, patient_name={patient_name}, duration={duration:.2f})")
            
            return str(report_path), patient_name, duration

        except Exception as e:
            logger.error(f"Case processing failed: {e}")
            raise

    def cleanup_temp_files(self, case_output_dir: Optional[Path] = None) -> None:
        """
        Clean up temporary files created during processing.

        Args:
            case_output_dir: Specific case directory to clean, or None for all temp files
        """
        try:
            if case_output_dir:
                # Clean specific case directory
                if case_output_dir.exists():
                    import shutil
                    shutil.rmtree(case_output_dir)
                    logger.info(f"Cleaned up temporary files: {case_output_dir}")
            else:
                # Clean all temp files
                if self.config.paths.temp_output_dir.exists():
                    import shutil
                    shutil.rmtree(self.config.paths.temp_output_dir)
                    self.config.paths.temp_output_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("Cleaned up all temporary files")

        except Exception as e:
            logger.warning(f"Failed to cleanup temporary files: {e}")