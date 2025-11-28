# Setup Guide - Configuration Files & Templates

This document contains all the configuration files and setup scripts that need to be created when implementing the system.

## 1. config.yaml

Create this file in the project root:

```yaml
# Ultrasound Report Generator - Main Configuration File

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
paths:
  templates_docx: "US Report templates.docx"
  templates_json: "data/templates.json"
  samples_dir: "samples"
  temp_output_dir: "temp/processed_images"
  logs_dir: "logs"
  outputs_dir: "outputs/reports"

# ============================================================================
# DICOM PROCESSING CONFIGURATION
# ============================================================================
dicom:
  output_format: "jpg"
  output_quality: 95
  target_resolution: [1024, 768]
  preserve_metadata: true
  max_concurrent_conversions: 5

# ============================================================================
# PHI REMOVAL CONFIGURATION
# ============================================================================
phi_removal:
  method: "crop"  # Options: "crop", "ocr", "hybrid"
  
  # Crop method settings
  crop_pixels: 53  # Pixels to crop from top of image
  
  # OCR method settings
  ocr_enabled: true
  ocr_engine: "tesseract"  # Options: "tesseract", "easyocr"
  ocr_languages: ["eng"]
  text_detection_confidence: 0.6
  
  # Hybrid method settings
  hybrid_min_text_threshold: 3  # Minimum text regions to use OCR

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
llm:
  provider: "openrouter"
  model: "google/gemini-2.0-flash-exp:free"
  
  # API settings
  base_url: "https://openrouter.ai/api/v1"
  max_tokens: 4000
  temperature: 0.3
  top_p: 0.9
  timeout: 120
  max_retries: 3
  retry_delay: 2
  
  # Image handling
  max_images_per_request: 10
  image_encoding: "base64"
  
  # Prompt engineering
  system_prompt_enabled: true
  few_shot_examples: 1
  include_template_structure: true

# ============================================================================
# TEMPLATE SELECTION CONFIGURATION
# ============================================================================
template_mapping:
  # Single modality mappings
  "Us_Breast_(Bilateral)": "ULTRASOUND OF BOTH BREASTS"
  "Us_Breast_(Right)": "ULTRASOUND OF RIGHT BREAST"
  "Us_Breast_(Left)": "ULTRASOUND OF LEFT BREAST"
  "Us_Liver": "ULTRASOUND SCAN OF LIVER"
  "Us_Gallbladder": "ULTRASOUND SCAN OF GALLBLADDER"
  "Us_Liver_GB_Biliary": "ULTRASOUND SCAN OF LIVER, GALLBLADDER AND BILIARY SYSTEM"
  "Us_Kidneys": "ULTRASOUND OF KIDNEYS"
  "Us_Upper_Abdomen": "ULTRASOUND SCAN OF UPPER ABDOMEN"
  "Us_Abdomen_Pelvis": "ULTRASOUND SCAN OF ABDOMEN AND PELVIS"
  "Us_Thyroid": "ULTRASOUND OF THYROID GLAND"
  "Us_Neck": "ULTRASOUND OF NECK"
  "Us_Carotid": "DUPLEX ULTRASOUND OF CAROTID ARTERIES"
  "Us_Scrotum": "ULTRASOUND OF SCROTUM"
  "Us_Prostate": "ULTRASOUND OF THE URINARY BLADDER AND PROSTATE"
  "Us_Pelvis": "ULTRASOUND SCAN OF THE PELVIS"
  "Us_Obstetric": "ULTRASOUND SCAN OF OBSTETRICS"
  "Us_Infant_Brain": "ULTRASOUND INFANT BRAIN"
  "Us_Infant_Spine": "ULTRASOUND OF INFANT SPINE"
  "Us_Infant_Hips": "ULTRASOUND OF BOTH HIPS FOR DEVELOPMENTAL HIP DYSPLASIA"
  "Doppler_Lower_Limb": "DOPPLER ULTRASOUND OF LOWER LIMB VEINS"
  "Echo_TTE": "TRANSTHORACIC ECHOCARDIOGRAM REPORT"
  
  # Multi-modality mappings (combined studies)
  "Us_Breast_(Bilateral)|Mg2DBi": "BILATERAL 2D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"
  "Us_Breast_(Right)|Mg2D_Right": "DIGITAL 2D MAMMOGRAM & ULTRASOUND OF RIGHT BREAST"
  "Us_Breast_(Bilateral)|Mg3DBi_Standard_Screening__Tomohd": "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"
  "Us_Breast_(Right)|Mg3D_Right": "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF RIGHT BREAST"

# Fallback template selection
template_selection:
  use_fuzzy_matching: true
  fuzzy_threshold: 0.7
  prompt_on_ambiguous: true
  default_template: "ULTRASOUND OF BOTH BREASTS"

# ============================================================================
# USER INTERFACE CONFIGURATION
# ============================================================================
ui:
  title: "Ultrasound Report Generator"
  theme: "light"
  max_upload_size_mb: 500
  preview_images: true
  max_preview_images: 10
  preview_thumbnail_size: [200, 150]
  enable_report_editing: true
  show_performance_metrics: true

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================
performance:
  enable_profiling: true
  profile_output: "logs/performance.json"
  max_concurrent_images: 5
  batch_size: 10
  cache_templates: true
  cleanup_temp_files: true

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "logs/app.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
  console_output: true
  file_output: true

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================
export:
  default_format: "docx"  # docx, txt, both
  docx_template: null  # Optional custom DOCX template
  include_metadata: true
  include_timestamp: true
  include_performance_stats: false
  filename_pattern: "Report_{patient_id}_{timestamp}.{ext}"

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================
validation:
  validate_dicom_files: true
  require_template_match: false
  check_image_quality: true
  min_image_resolution: [512, 384]
  max_case_images: 100
```

---

## 2. .env.template

Create this file as a template for users:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_api_key_here

# Optional: Custom API endpoint
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional: Your app name and URL for OpenRouter
# OPENROUTER_APP_NAME=Ultrasound Report Generator
# OPENROUTER_APP_URL=https://your-app-url.com

# --- Google Sheets Audit Logging (for cloud deployment) ---
# This is required for persistent audit trails on Streamlit Community Cloud.
# 1. Create a Google Cloud Platform (GCP) project and enable the Google Sheets and Google Drive APIs.
# 2. Create a service account and download its JSON key file.
# 3. Share your target Google Sheet with the service account's email address.
# 4. Paste the entire content of the JSON key file into this variable.
# Example: GCP_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": ...}'
GCP_SERVICE_ACCOUNT_JSON=
```

---

## 3. requirements.txt

```txt
# Core Dependencies
python-dotenv==1.0.0
pyyaml==6.0.1
pydantic==2.5.3

# DICOM Processing
pydicom==2.4.4
Pillow==10.1.0
numpy==1.26.2

# OCR for PHI Removal
pytesseract==0.3.10

# Template Management
python-docx==1.1.0

# LLM Integration
openai==1.6.1
requests==2.31.0
httpx==0.25.2

# UI Framework
streamlit==1.29.0
streamlit-extras==0.3.6

# Utilities
loguru==0.7.2
tqdm==4.66.1

# Data Handling
pandas==2.1.4

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Development Tools
black==23.12.1
flake8==7.0.0
mypy==1.7.1
```

---

## 4. .gitignore

```gitignore
# Python
*.py[cod]
*$py.class
__pycache__/
*.so
.Python
venv/
env/
ENV/
.venv

# Environment variables
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Project specific
temp/
logs/
outputs/
*.dcm
data/templates.json
*.log

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/

# Distribution / packaging
build/
dist/
*.egg-info/
*.egg

# Jupyter Notebook
.ipynb_checkpoints

# OS
Thumbs.db
.DS_Store
```

---

## 5. scripts/extract_templates.py

Template extraction script:

```python
#!/usr/bin/env python3
"""
Template Extraction Script

Extracts all report templates from the Word document and saves to JSON.
Run this once during initial setup.

Usage:
    python scripts/extract_templates.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config_manager import ConfigManager
from src.templates.template_extractor import TemplateExtractor
from src.utils.logger import LoggerManager

def main():
    """Extract templates from Word document"""
    
    # Initialize
    config = ConfigManager("config.yaml")
    logger = LoggerManager(config.paths.logs_dir, level="INFO")
    log = logger.get_logger(__name__)
    
    log.info("Starting template extraction...")
    
    # Check if templates.docx exists
    if not config.paths.templates_docx.exists():
        log.error(f"Template file not found: {config.paths.templates_docx}")
        return 1
    
    # Extract templates
    try:
        extractor = TemplateExtractor()
        templates = extractor.extract_from_docx(config.paths.templates_docx)
        
        log.info(f"Extracted {len(templates)} templates")
        
        # Save to JSON
        extractor.save_to_json(templates, config.paths.templates_json)
        log.info(f"Saved templates to {config.paths.templates_json}")
        
        # Print summary
        print(f"\n✓ Successfully extracted {len(templates)} templates:")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template.name}")
        
        return 0
        
    except Exception as e:
        log.error(f"Template extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. scripts/setup_tesseract.py

Tesseract verification script:

```python
#!/usr/bin/env python3
"""
Tesseract OCR Setup Verification

Checks if Tesseract OCR is properly installed and configured.

Usage:
    python scripts/setup_tesseract.py
"""

import sys
import subprocess
from pathlib import Path

def check_tesseract():
    """Check Tesseract installation"""
    
    print("Checking Tesseract OCR installation...\n")
    
    try:
        import pytesseract
        
        # Get version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        
        # Get available languages
        langs = pytesseract.get_languages()
        print(f"✓ Available languages: {', '.join(langs)}")
        
        # Test OCR
        from PIL import Image, ImageDraw, ImageFont
        
        # Create test image with text
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR", fill='black')
        
        # Run OCR
        text = pytesseract.image_to_string(img)
        
        if "Test" in text or "OCR" in text:
            print("✓ OCR test passed\n")
            print("Tesseract is properly configured!")
            return 0
        else:
            print("⚠ OCR test failed - text not detected correctly")
            print(f"Detected: {text}")
            return 1
            
    except ImportError:
        print("✗ pytesseract not installed")
        print("Run: pip install pytesseract")
        return 1
        
    except Exception as e:
        print(f"✗ Tesseract not found or not configured properly")
        print(f"Error: {e}\n")
        print("Installation instructions:")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  macOS: brew install tesseract")
        print("  Linux: sudo apt-get install tesseract-ocr")
        return 1

if __name__ == "__main__":
    sys.exit(check_tesseract())
```

---

## 7. scripts/test_openrouter.py

OpenRouter API test script:

```python
#!/usr/bin/env python3
"""
OpenRouter API Test

Tests connection to OpenRouter API and validates credentials.

Usage:
    python scripts/test_openrouter.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

def test_openrouter():
    """Test OpenRouter API connection"""
    
    print("Testing OpenRouter API connection...\n")
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("✗ OPENROUTER_API_KEY not found in .env file")
        print("Please create a .env file with your API key")
        return 1
    
    print(f"✓ API key found: {api_key[:10]}...")
    
    # Test API connection
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/your-repo",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            print(f"✓ API connection successful")
            print(f"✓ Available models: {len(models.get('data', []))}\n")
            
            # Check if target model is available
            target_model = "google/gemini-2.0-flash-exp:free"
            model_ids = [m['id'] for m in models.get('data', [])]
            
            if target_model in model_ids:
                print(f"✓ Target model available: {target_model}")
            else:
                print(f"⚠ Target model not found: {target_model}")
                print("Available free models:")
                for model in models.get('data', []):
                    if 'free' in model['id']:
                        print(f"  - {model['id']}")
            
            print("\nOpenRouter API is properly configured!")
            return 0
            
        else:
            print(f"✗ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return 1
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_openrouter())
```

---

## 8. Setup Instructions

### Step-by-Step Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR** (system-level):
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

4. **Create .env file:**
```bash
cp .env.template .env
# Edit .env and add your OpenRouter API key
```

5. **Verify setup:**
```bash
python scripts/setup_tesseract.py
python scripts/test_openrouter.py
```

6. **Extract templates:**
```bash
python scripts/extract_templates.py
```

7. **Launch application:**
```bash
streamlit run src/ui/app.py
```

---

## 9. Directory Creation

Create all necessary directories:

```bash
mkdir -p src/{core,processors,templates,llm,generators,ui,utils}
mkdir -p data
mkdir -p temp/processed_images
mkdir -p logs
mkdir -p outputs/reports
mkdir -p tests
mkdir -p scripts

# Create __init__.py files
touch src/__init__.py
touch src/{core,processors,templates,llm,generators,ui,utils}/__init__.py
touch tests/__init__.py
```

---

## 10. First Run Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Tesseract OCR installed and verified
- [ ] .env file created with API key
- [ ] OpenRouter API connection tested
- [ ] Templates extracted from Word document
- [ ] All directories created
- [ ] Application launches successfully

---

## Next Steps

Once setup is complete, proceed to implementation in Code mode following the `IMPLEMENTATION_PLAN.md`.