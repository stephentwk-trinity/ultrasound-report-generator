from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Template:
    id: str
    name: str
    sections: Dict[str, str]  # section_name -> content/structure
    metadata: Dict[str, Any]