import sys
from pathlib import Path

# Add project root to Python path for Streamlit Cloud
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

"""
Ultrasound Report Generator - Streamlit Web Interface

This module provides a web-based user interface for processing ultrasound DICOM
images and generating medical reports using AI.
"""

import streamlit as st
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import traceback

from src.core.orchestrator import CaseOrchestrator
from src.utils.logger import LoggerManager

# Initialize logger
logger = LoggerManager.get_logger(__name__)


def extract_zip_file(zip_file, extract_to: Path) -> Optional[Path]:
    """
    Extract a zip file to a temporary directory.
    
    Args:
        zip_file: Uploaded file object from Streamlit
        extract_to: Directory to extract files to
        
    Returns:
        Path to the extracted directory, or None if extraction failed
    """
    try:
        # Save uploaded file to temporary location
        temp_zip_path = extract_to / zip_file.name
        with open(temp_zip_path, 'wb') as f:
            f.write(zip_file.getbuffer())
        
        # Extract zip file
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Remove the zip file after extraction
        temp_zip_path.unlink()
        
        # Find the top-level directory containing the DICOM files
        # Look for directories that contain subdirectories with .dcm files
        extracted_dirs = [d for d in extract_to.iterdir() if d.is_dir()]
        
        if extracted_dirs:
            # Return the first directory (usually the patient case folder)
            return extracted_dirs[0]
        else:
            # If no subdirectories, return the extraction directory itself
            return extract_to
            
    except Exception as e:
        logger.error(f"Failed to extract {zip_file.name}: {e}")
        return None


def get_patient_name_from_path(case_path: Path) -> str:
    """
    Extract patient name or identifier from the case directory path.
    
    Args:
        case_path: Path to the case directory
        
    Returns:
        Patient name or identifier
    """
    # Use the directory name as the patient identifier
    return case_path.name


def read_report_file(report_path: str) -> str:
    """
    Read the generated report from file.
    
    Args:
        report_path: Path to the report file
        
    Returns:
        Report text content
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read report file {report_path}: {e}")
        return f"Error reading report: {str(e)}"


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Ultrasound Report Generator",
        page_icon="🏥",
        layout="wide"
    )
    
    # Application title
    st.title("🏥 Ultrasound Report Generator")
    st.markdown("---")
    
    # Instructions
    with st.expander("ℹ️ Instructions", expanded=False):
        st.markdown("""
        ### How to use this application:
        
        1. **Upload ZIP files** containing DICOM ultrasound images
        2. Click **"Start Processing"** to generate reports
        3. Wait for processing to complete (progress bar will show status)
        4. Review and copy the generated reports from the text areas below
        
        **Note:** Each ZIP file should contain a patient case with DICOM (.dcm) files organized in folders. (e.g. patient_name.zip => patient_name => Us_Breast_(Bilateral) - US23__USBREAST => US_BREAST_(BILATERAL)_1 => DICOM images)
        """)
    
    st.markdown("##")
    
    # File uploader for multiple ZIP files
    uploaded_files = st.file_uploader(
        "Upload ZIP files containing DICOM images",
        type=['zip'],
        accept_multiple_files=True,
        help="Select one or more ZIP files containing patient ultrasound DICOM images"
    )
    
    # Show uploaded files and prior report text areas
    prior_reports = {}
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        
        st.markdown("### 📁 Uploaded Files & Prior Reports")
        st.markdown("*Optionally paste prior reports for comparison. Leave blank if no prior report is available.*")
        
        for i, file in enumerate(uploaded_files, 1):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{i}. {file.name}**")
                st.caption(f"Size: {file.size / 1024:.1f} KB")
            with col2:
                prior_report_text = st.text_area(
                    label=f"Prior Report for {file.name}",
                    value="",
                    height=150,
                    key=f"prior_report_{file.name}",
                    placeholder="Paste prior report text here (optional)...",
                    help="If a prior report exists for this patient, paste it here for comparison in the generated report."
                )
                prior_reports[file.name] = prior_report_text
            st.markdown("---")
    
    st.markdown("##")
    
    # Start processing button
    start_processing = st.button(
        "🚀 Start Processing",
        type="primary",
        disabled=not uploaded_files,
        use_container_width=True
    )
    
    # Processing logic
    if start_processing and uploaded_files:
        # Create a container for processing status
        status_container = st.container()
        
        with status_container:
            st.info("⚙️ Processing started...")
            
            # Progress bar
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # List to store results (patient_name, report_text, success, duration)
            results: List[Tuple[str, str, bool, float]] = []
            
            # Create temporary directory for all extractions
            with tempfile.TemporaryDirectory() as temp_base_dir:
                temp_base_path = Path(temp_base_dir)
                
                # Initialize orchestrator
                try:
                    orchestrator = CaseOrchestrator("config.yaml")
                    st.success("✅ System initialized successfully")
                except Exception as e:
                    st.error(f"❌ Failed to initialize system: {str(e)}")
                    logger.error(f"Orchestrator initialization failed: {traceback.format_exc()}")
                    return
                
                # Process each uploaded file
                for i, zip_file in enumerate(uploaded_files):
                    # Update progress
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    progress_text.text(f"Processing {i + 1} of {len(uploaded_files)}: {zip_file.name}")
                    
                    # Create unique directory for this case
                    case_temp_dir = temp_base_path / f"case_{i}"
                    case_temp_dir.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        # Extract ZIP file
                        logger.info(f"Extracting {zip_file.name}")
                        case_path = extract_zip_file(zip_file, case_temp_dir)
                        
                        if case_path is None:
                            results.append((zip_file.name, "Failed to extract ZIP file", False, 0.0))
                            continue
                        
                        # Get prior report for this file (if any)
                        prior_report = prior_reports.get(zip_file.name, "").strip() or None
                        
                        # Process the case using orchestrator (now returns tuple with duration)
                        report_path, patient_name, duration = orchestrator.process_case(
                            str(case_path),
                            prior_report=prior_report
                        )
                        logger.info(f"Processing case: {patient_name}" + (" with prior report" if prior_report else ""))
                        
                        # Read the generated report
                        report_text = read_report_file(report_path)
                        
                        # Store successful result with duration
                        results.append((patient_name, report_text, True, duration))
                        logger.info(f"Successfully processed case: {patient_name} in {duration:.2f} seconds")
                        
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        logger.error(f"Failed to process {zip_file.name}: {traceback.format_exc()}")
                        results.append((zip_file.name, error_msg, False, 0.0))
            
            # Clear progress indicators
            progress_bar.empty()
            progress_text.empty()
        
        # Display results
        st.markdown("---")
        st.markdown("## 📋 Generated Reports")
        
        if not results:
            st.warning("⚠️ No reports were generated")
        else:
            # Summary
            successful = sum(1 for _, _, success, _ in results if success)
            failed = len(results) - successful
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Cases", len(results))
            with col2:
                st.metric("Successful", successful, delta_color="normal")
            with col3:
                st.metric("Failed", failed, delta_color="inverse")
            
            st.markdown("##")
            
            # Display each report
            for patient_name, report_text, success, duration in results:
                if success:
                    st.subheader(f"👤 {patient_name}")
                    
                    # Display processing time
                    st.metric("Processing Time", f"{duration:.2f} seconds")
                    
                    # Display report in a text area for easy copying
                    st.text_area(
                        label="Report",
                        value=report_text,
                        height=400,
                        key=f"report_{patient_name}",
                        help="Click inside to select all text, then copy (Ctrl+C or Cmd+C)"
                    )
                    
                    # Download button for the report
                    st.download_button(
                        label="📥 Download Report",
                        data=report_text,
                        file_name=f"{patient_name}_report.txt",
                        mime="text/plain",
                        key=f"download_{patient_name}"
                    )
                    
                    st.markdown("---")
                else:
                    # Show error for failed cases
                    with st.expander(f"❌ **{patient_name}** (Processing Failed)", expanded=False):
                        st.error(report_text)
        
        st.success("✅ All processing completed!")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
        "Ultrasound Report Generator | Powered by AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()