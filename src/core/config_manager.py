import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import os

@dataclass
class PathConfig:
    templates_docx: Path
    templates_json: Path
    samples_dir: Path
    temp_output_dir: Path
    logs_dir: Path
    outputs_dir: Path

@dataclass
class DicomConfig:
    output_format: str = "jpg"
    output_quality: int = 95
    target_resolution: tuple = (1024, 768)

@dataclass
class PhiRemovalConfig:
    method: str = "crop"  # crop, ocr, hybrid
    crop_percentage: float = 0.07
    ocr_enabled: bool = True
    ocr_engine: str = "tesseract"
    ocr_languages: list = field(default_factory=lambda: ["eng"])
    text_detection_confidence: float = 0.6

@dataclass
class LlmConfig:
    provider: str = "openrouter"
    model: str = "google/gemini-2.5-pro"  # also change the model name in line 115 just in case
    max_tokens: int = 4000
    temperature: float = 0.3
    timeout: int = 120
    api_key: Optional[str] = None

class ConfigManager:
    """Centralized configuration management"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        self._validate_config()

        # Load environment variables
        load_dotenv()

        # Initialize configuration objects
        self.paths = self._init_path_config()
        self.dicom = self._init_dicom_config()
        self.phi_removal = self._init_phi_config()
        self.llm = self._init_llm_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = ['paths', 'dicom', 'phi_removal', 'llm']
        for section in required_sections:
            if section not in self.config_data:
                raise ValueError(f"Missing required config section: {section}")

    def _init_path_config(self) -> PathConfig:
        """Initialize path configuration"""
        paths = self.config_data['paths']
        return PathConfig(
            templates_docx=Path(paths['templates_docx']),
            templates_json=Path(paths['templates_json']),
            samples_dir=Path(paths['samples_dir']),
            temp_output_dir=Path(paths['temp_output_dir']),
            logs_dir=Path(paths['logs_dir']),
            outputs_dir=Path(paths.get('outputs_dir', 'outputs/reports'))
        )

    def _init_dicom_config(self) -> DicomConfig:
        """Initialize DICOM configuration"""
        dicom = self.config_data['dicom']
        return DicomConfig(
            output_format=dicom.get('output_format', 'jpg'),
            output_quality=dicom.get('output_quality', 95),
            target_resolution=tuple(dicom.get('target_resolution', [1024, 768]))
        )

    def _init_phi_config(self) -> PhiRemovalConfig:
        """Initialize PHI removal configuration"""
        phi = self.config_data['phi_removal']
        return PhiRemovalConfig(
            method=phi.get('method', 'crop'),
            crop_percentage=phi.get('crop_percentage', 0.07),
            ocr_enabled=phi.get('ocr_enabled', True),
            ocr_engine=phi.get('ocr_engine', 'tesseract'),
            ocr_languages=phi.get('ocr_languages', ['eng']),
            text_detection_confidence=phi.get('text_detection_confidence', 0.6)
        )

    def _init_llm_config(self) -> LlmConfig:
        """Initialize LLM configuration"""
        llm = self.config_data['llm']

        # Get API key from environment or config
        api_key = os.getenv('OPENROUTER_API_KEY') or llm.get('api_key')

        return LlmConfig(
            provider=llm.get('provider', 'openrouter'),
            model=llm.get('model', 'google/gemini-2.5-pro'),
            max_tokens=llm.get('max_tokens', 4000),
            temperature=llm.get('temperature', 0.3),
            timeout=llm.get('timeout', 120),
            api_key=api_key
        )

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(section, {}).get(key, default)

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.paths.temp_output_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        Path(self.paths.templates_json).parent.mkdir(parents=True, exist_ok=True)