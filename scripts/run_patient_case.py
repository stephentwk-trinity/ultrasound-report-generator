#!/usr/bin/env python3
"""
Master test script for running a complete patient case through the Ultrasound Report Generator.

This script demonstrates the end-to-end workflow:
1. Initialize CaseOrchestrator
2. Process DICOM files from samples/dicom_images_patient_1
3. Generate final report
4. Log progress and display results
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core.orchestrator import CaseOrchestrator
from src.utils.logger import LoggerManager

# Initialize logger
logger = LoggerManager.get_logger(__name__)


def main():
    """Main execution function."""
    try:
        logger.info("Starting Ultrasound Report Generator - Patient Case Test")

        # Initialize the orchestrator
        logger.info("Initializing CaseOrchestrator...")
        orchestrator = CaseOrchestrator()

        # Define input directory
        input_dir = "samples/dicom_images_patient_1"
        logger.info(f"Processing patient case from: {input_dir}")

        # Verify input directory exists
        if not Path(input_dir).exists():
            raise FileNotFoundError(f"Sample data directory not found: {input_dir}")

        # Process the case
        logger.info("Starting case processing...")
        report_path = orchestrator.process_case(input_dir)

        # Success!
        logger.info("=" * 60)
        logger.info("CASE PROCESSING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Final report generated: {report_path}")
        logger.info("=" * 60)

        # Display report contents
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()

            logger.info("Report Contents:")
            logger.info("-" * 40)
            print(report_content)
            logger.info("-" * 40)

        except Exception as e:
            logger.warning(f"Could not display report contents: {e}")

        return True

    except Exception as e:
        logger.error(f"Case processing failed: {e}")
        logger.error("See logs for detailed error information")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)