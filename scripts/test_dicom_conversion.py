#!/usr/bin/env python3
"""
Test script for DicomProcessor module.
Converts sample DICOM images to JPG format.
"""

from pathlib import Path
from src.processors.dicom_processor import DicomProcessor
from src.core.config_manager import ConfigManager

def main():
    # Load project configuration
    config_manager = ConfigManager()

    # Instantiate DicomProcessor
    dicom_processor = DicomProcessor(config_manager)

    # Define input and output directories
    input_dir = Path("samples/dicom_images_patient_1")
    output_dir = Path("temp/test_conversion_output")

    # Process the directory
    jpg_paths = dicom_processor.process_directory(input_dir, output_dir)

    # Print confirmation message
    print(f"Conversion completed. Processed {len(jpg_paths)} files.")
    print(f"Output JPGs can be found in: {output_dir}")

if __name__ == "__main__":
    main()