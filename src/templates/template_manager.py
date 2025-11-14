import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from thefuzz import fuzz
from .template_model import Template


class TemplateManager:
    """
    Manages loading and accessing ultrasound report templates.
    """

    def __init__(self, templates_path: str = "data/templates.json"):
        """
        Initialize the TemplateManager with the path to the templates JSON file.

        Args:
            templates_path: Path to the templates JSON file
        """
        self.templates_path = Path(templates_path)
        self.templates: List[Template] = []
        self.templates_by_id: Dict[str, Template] = {}
        self.templates_by_name: Dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Load templates from the JSON file and populate internal data structures.
        """
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)

            for template_data in templates_data:
                template = Template(
                    id=template_data['id'],
                    name=template_data['name'],
                    sections=template_data['sections'],
                    metadata=template_data['metadata']
                )
                self.templates.append(template)
                self.templates_by_id[template.id] = template
                self.templates_by_name[template.name] = template

        except FileNotFoundError:
            raise FileNotFoundError(f"Templates file not found: {self.templates_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in templates file: {e}")

    def get_template_by_id(self, template_id: str) -> Template:
        """
        Get a template by its ID.

        Args:
            template_id: The template ID

        Returns:
            The Template object

        Raises:
            KeyError: If template ID not found
        """
        if template_id not in self.templates_by_id:
            raise KeyError(f"Template with ID '{template_id}' not found")
        return self.templates_by_id[template_id]

    def get_template_by_name(self, template_name: str) -> Template:
        """
        Get a template by its name.

        Args:
            template_name: The template name

        Returns:
            The Template object

        Raises:
            KeyError: If template name not found
        """
        if template_name not in self.templates_by_name:
            raise KeyError(f"Template with name '{template_name}' not found")
        return self.templates_by_name[template_name]

    def get_all_templates(self) -> List[Template]:
        """
        Get all loaded templates.

        Returns:
            List of all Template objects
        """
        return self.templates.copy()

    def get_template_names(self) -> List[str]:
        """
        Get a list of all template names.

        Returns:
            List of template names
        """
        return list(self.templates_by_name.keys())

    def get_template_ids(self) -> List[str]:
        """
        Get a list of all template IDs.

        Returns:
            List of template IDs
        """
        return list(self.templates_by_id.keys())


class TemplateSelector:
    """
    Selects appropriate templates based on directory names using rule-based pattern matching.
    """

    def __init__(self, template_manager: TemplateManager):
        """
        Initialize the TemplateSelector.

        Args:
            template_manager: Instance of TemplateManager
        """
        self.template_manager = template_manager

    def _parse_directory_names(self, directory_names: List[str]) -> Dict[str, Any]:
        """
        Parse directory names to extract modality and study type information.

        Args:
            directory_names: List of directory names

        Returns:
            Dictionary with parsed information
        """
        info = {
            'has_us_breast': False,
            'has_us_breast_bilateral': False,
            'has_us_breast_right': False,
            'has_us_breast_left': False,
            'has_mg_2d': False,
            'has_mg_3d': False,
            'has_mg_bilateral': False,
            'has_mg_right': False,
            'has_mg_left': False,
        }

        for dir_name in directory_names:
            dir_upper = dir_name.upper()

            # Check for Ultrasound Breast
            if 'BREAST' in dir_upper or 'USBREAST' in dir_upper:
                info['has_us_breast'] = True
                
                if 'BILATERAL' in dir_upper or '(BILATERAL)' in dir_upper:
                    info['has_us_breast_bilateral'] = True
                elif 'RIGHT' in dir_upper or '(RIGHT)' in dir_upper:
                    info['has_us_breast_right'] = True
                elif 'LEFT' in dir_upper or '(LEFT)' in dir_upper:
                    info['has_us_breast_left'] = True
                # Default to bilateral if not specified
                elif 'US_BREAST' in dir_upper or 'USBREAST' in dir_upper:
                    info['has_us_breast_bilateral'] = True

            # Check for Mammogram
            if 'MG' in dir_upper or 'MMG' in dir_upper or 'MAMMOGRAM' in dir_upper:
                # Check for 2D first (more specific markers like _2D_ or BI02)
                if 'MG2D' in dir_upper or '_2D_' in dir_upper or '2D_MMG' in dir_upper or 'BI02' in dir_upper:
                    info['has_mg_2d'] = True
                # Check for 3D only if 2D not detected
                elif 'MG3D' in dir_upper or 'TOMO' in dir_upper or 'MG3DBI' in dir_upper:
                    info['has_mg_3d'] = True
                
                # Check for bilateral/right/left
                if 'BI' in dir_upper or 'BILATERAL' in dir_upper or 'BIL' in dir_upper:
                    info['has_mg_bilateral'] = True
                elif 'RIGHT' in dir_upper:
                    info['has_mg_right'] = True
                elif 'LEFT' in dir_upper:
                    info['has_mg_left'] = True

        return info

    def select_template(self, directory_names: List[str]) -> Optional[Template]:
        """
        Select the appropriate template based on directory names.

        Args:
            directory_names: List of directory names (can be single or multiple for combined studies)

        Returns:
            The matching Template object, or None if no match found
        """
        # Handle both single string and list input
        if isinstance(directory_names, str):
            directory_names = [directory_names]

        info = self._parse_directory_names(directory_names)

        # Determine template based on modality combinations
        template_name = None

        # Combined Mammogram + US studies (priority)
        if info['has_us_breast'] and info['has_mg_3d']:
            if info['has_us_breast_bilateral'] or info['has_mg_bilateral']:
                template_name = "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"
            elif info['has_us_breast_right'] or info['has_mg_right']:
                template_name = "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF _RIGHT BREAST"
            else:
                template_name = "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"

        elif info['has_us_breast'] and info['has_mg_2d']:
            if info['has_us_breast_bilateral'] or info['has_mg_bilateral']:
                template_name = "BILATERAL 2D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"
            elif info['has_us_breast_right'] or info['has_mg_right']:
                template_name = "DIGITAL 2D MAMMOGRAM & ULTRASOUND OF RIGHT BREAST"
            else:
                template_name = "BILATERAL 2D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"

        # US only studies
        elif info['has_us_breast']:
            # Note: There are no separate right/left breast templates in templates.json
            # All breast US studies use "ULTRASOUND OF BOTH BREASTS"
            template_name = "ULTRASOUND OF BOTH BREASTS"

        # Try to get the template
        if template_name:
            try:
                return self.template_manager.get_template_by_name(template_name)
            except KeyError:
                # Template not found, try fuzzy fallback
                return self._fuzzy_fallback(template_name)

        return None

    def _fuzzy_fallback(self, target_name: str) -> Optional[Template]:
        """
        Fallback to fuzzy matching if exact match fails.

        Args:
            target_name: Target template name

        Returns:
            Best matching template or None
        """
        best_match = None
        best_score = 0.0
        threshold = 0.8

        template_names = self.template_manager.get_template_names()

        for template_name in template_names:
            score = fuzz.ratio(target_name.lower(), template_name.lower()) / 100.0

            if score > best_score and score >= threshold:
                best_score = score
                best_match = self.template_manager.get_template_by_name(template_name)

        return best_match

    def select_template_with_info(self, directory_names: List[str]) -> tuple[Optional[Template], Dict[str, Any]]:
        """
        Select template and return detailed parsing information.

        Args:
            directory_names: List of directory names

        Returns:
            Tuple of (Template object or None, parsing info dictionary)
        """
        if isinstance(directory_names, str):
            directory_names = [directory_names]

        info = self._parse_directory_names(directory_names)
        template = self.select_template(directory_names)

        return template, info