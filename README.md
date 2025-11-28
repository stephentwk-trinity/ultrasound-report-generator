# 🏥 Ultrasound Report Generator

An AI-powered application for automated generation of initial radiology reports from DICOM ultrasound images using multimodal language models.

## 🌟 Features

- **Automated DICOM Processing**: Recursively scans directories, converts DICOM files to high-quality JPG images
- **Privacy-Focused PHI Removal**: Configurable removal of Protected Health Information using OCR or pixel cropping
- **Intelligent Template Selection**: Automatically selects appropriate report templates based on study folder structure
- **AI-Powered Report Generation**: Uses OpenRouter's multimodal LLMs (Gemini 2.0 Flash) with few-shot learning
- **47+ Medical Templates**: Comprehensive coverage of ultrasound examination types
- **User-Friendly Interface**: Streamlit-based web UI for easy interaction
- **Performance Tracking**: Built-in profiling to monitor processing times
- **Professional Export**: Save reports in DOCX or TXT format

## 📋 Prerequisites

### System Requirements
- Python 3.9 or higher
- 8GB RAM (16GB recommended)
- 5GB free disk space
- Internet connection (for LLM API calls)

### Required Software
- **Python**: Download from [python.org](https://www.python.org/)
- **Tesseract OCR** (for PHI removal):
  - **Windows**: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
  - **macOS**: `brew install tesseract`
  - **Linux**: `sudo apt-get install tesseract-ocr`

### API Access
- **OpenRouter API Key**: Sign up at [openrouter.ai](https://openrouter.ai/)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ultrasound-report-generator
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Application

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Edit `config.yaml` to customize settings (optional).

### 5. Extract Templates (First-Time Setup)

```bash
python scripts/extract_templates.py
```

This will parse the `US Report templates.docx` file and create `data/templates.json`.

### 6. Launch the Application

```bash
streamlit run src/ui/app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## 📖 Usage Guide

### Processing a Patient Case

1. **Select Case Directory**
   - Click the directory browser in the UI
   - Navigate to the patient's DICOM folder
   - The folder structure should contain examination subdirectories (e.g., `Us_Breast_(Bilateral) - US23__USBREAST`)

2. **Add Optional Information** (if available)
   - Previous reports from referral hospitals
   - Clinical information or indications
   - These help the AI generate more contextual reports

3. **Generate Report**
   - Click the "Generate Report" button
   - Monitor progress through the status messages
   - View processed images in the preview section

4. **Review & Export**
   - Review the generated report sections
   - Make any necessary edits (if enabled)
   - Export to DOCX or TXT format
   - Save to your desired location

### Folder Structure Requirements

Patient case folders should follow this structure:

```
Patient_Case_Folder/
├── Us_Breast_(Bilateral) - US23__USBREAST/
│   └── US_BREAST_(BILATERAL)_1/
│       ├── IM-0001-0001.dcm
│       ├── IM-0001-0002.dcm
│       └── ...
└── [Optional] Mg3DBi_Standard_Screening__Tomohd/
    └── ...
```

The application uses subfolder names to automatically select the appropriate report template.

## ⚙️ Configuration

### config.yaml

The main configuration file controls all system behavior:

```yaml
# DICOM Processing
dicom:
  output_format: "jpg"
  output_quality: 95
  target_resolution: [1024, 768]

# PHI Removal
phi_removal:
  method: "crop"  # Options: crop, ocr, hybrid
  crop_pixels: 53
  ocr_enabled: true

# LLM Configuration
llm:
  model: "google/gemini-2.0-flash-exp:free"
  max_tokens: 4000
  temperature: 0.3
```

### PHI Removal Methods

1. **Crop** (Default): Fast, removes top 53 pixels
2. **OCR**: Uses Tesseract to detect and redact text
3. **Hybrid**: Tries OCR first, falls back to crop

Choose based on your image consistency and privacy requirements.

## 🗂️ Project Structure

```
ultrasound-report-generator/
├── config.yaml              # Configuration file
├── .env                     # API keys (create this)
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── ARCHITECTURE.md         # Detailed system architecture
├── IMPLEMENTATION_PLAN.md  # Development guide
│
├── data/
│   └── templates.json      # Extracted report templates
│
├── samples/                # Example cases for AI training
│   ├── dicom_images_patient_1/
│   └── radiologist_completed_report_patient_1.docx
│
├── src/
│   ├── core/              # Core system components
│   ├── processors/        # DICOM & PHI processing
│   ├── templates/         # Template management
│   ├── llm/              # LLM integration
│   ├── generators/        # Report generation
│   ├── ui/               # User interface
│   └── utils/            # Utilities
│
├── temp/                  # Temporary files (auto-created)
├── logs/                  # Application logs (auto-created)
└── outputs/              # Generated reports (auto-created)
```

## 🔒 Privacy & Security

This application is designed with healthcare data privacy in mind:

- **Local Processing**: All image processing happens on your computer
- **No Cloud OCR**: Uses local Tesseract OCR instead of cloud services
- **Secure API Communication**: Only processed, de-identified images sent to LLM
- **Temporary File Cleanup**: Automatic deletion of temporary files
- **No Data Retention**: No patient data stored persistently

### Best Practices

1. **Store API keys securely** in `.env` file (never commit to Git)
2. **Review generated reports** before clinical use
3. **Clean temp directory** regularly
4. **Monitor logs** for any processing errors
5. **Keep system updated** with security patches

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_dicom_processor.py

# Run with coverage
pytest --cov=src tests/
```

## 📊 Performance Metrics

The application tracks performance for each report generation:

- DICOM scanning time
- Image conversion time
- PHI removal time
- LLM API call time
- Total end-to-end time

View metrics in the UI sidebar or check `logs/performance.json`.

## 🐛 Troubleshooting

### Common Issues

**1. Tesseract Not Found**
```
Error: Tesseract not found
```
Solution: Install Tesseract OCR and ensure it's in your system PATH.

**2. OpenRouter API Error**
```
Error: Invalid API key
```
Solution: Check your `.env` file contains the correct API key.

**3. DICOM Conversion Fails**
```
Error: Cannot convert DICOM
```
Solution: Verify DICOM files are valid. Try with a different image viewer first.

**4. Template Not Found**
```
Error: No matching template
```
Solution: Check folder naming matches the template mapping in `config.yaml`.

**5. Out of Memory**
```
Error: Memory allocation failed
```
Solution: Process fewer images at once. Adjust `max_concurrent_images` in config.

### Debug Mode

Enable debug logging in `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

Check `logs/app.log` for detailed information.

## 🤝 Contributing

This is a healthcare application. Contributions should maintain:

1. **Medical Accuracy**: Consult with radiologists
2. **Privacy Standards**: HIPAA/GDPR compliance
3. **Code Quality**: Type hints, tests, documentation
4. **Error Handling**: Graceful failure modes

## 📄 License

[Specify your license here]

## ⚠️ Disclaimer

**This application generates INITIAL radiology reports for review purposes only.**

- **Not FDA Approved**: This is not a certified medical device
- **Requires Review**: All AI-generated reports must be reviewed by qualified radiologists
- **No Clinical Decisions**: Do not make clinical decisions based solely on AI output
- **Use Responsibly**: Understand system limitations and potential errors

The developers assume no liability for medical decisions based on this software.

## 📞 Support

For issues, questions, or contributions:

- **GitHub Issues**: [Create an issue](link-to-issues)
- **Documentation**: See `ARCHITECTURE.md` for technical details
- **Email**: [your-email@domain.com]

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenRouter](https://openrouter.ai/)
- DICOM processing via [pydicom](https://pydicom.github.io/)
- OCR via [Tesseract](https://github.com/tesseract-ocr/tesseract)

## 📈 Roadmap

Future enhancements:

- [ ] Multi-language template support
- [ ] Batch processing mode
- [ ] PACS integration
- [ ] Voice dictation input
- [ ] Comparison with prior studies
- [ ] Custom template creation
- [ ] Mobile/tablet interface
- [ ] Offline LLM support

---

**App Version**: 1.2
**Last Updated**: 2025-11-28
**Prompt Version**: 1.1
**Last Updated**: 2025-11-27
**Status**: Development