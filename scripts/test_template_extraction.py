#!/usr/bin/env python3
"""
Test script for template extraction functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from templates.template_extractor import TemplateExtractor


def main():
    """Test the TemplateExtractor functionality."""
    print("Testing TemplateExtractor...")

    # Delete old templates.json if it exists
    json_path = Path("data/templates.json")
    if json_path.exists():
        print(f"Deleting old {json_path}...")
        os.remove(json_path)
        print("Old templates.json deleted successfully")

    # Initialize extractor
    extractor = TemplateExtractor()

    # Extract templates from Word document
    docx_path = Path("US Report templates.docx")
    print(f"\nExtracting templates from {docx_path}...")

    try:
        templates = extractor.extract_from_docx(docx_path)
        print(f"\n{'='*60}")
        print(f"Successfully extracted {len(templates)} templates")
        print(f"{'='*60}\n")

        # Show details of first 10 templates
        print("First 10 templates:")
        print("-" * 60)
        for i, template in enumerate(templates[:10]):
            variation_info = f" ({template.metadata.get('variation', 'N/A')})" if template.metadata.get('variation') else ""
            sections_list = list(template.sections.keys())
            print(f"{i+1}. {template.name}{variation_info}")
            print(f"   Sections: {sections_list}")
            print()

        # Save to JSON
        print(f"Saving templates to {json_path}...")
        extractor.save_to_json(templates, json_path)

        if json_path.exists():
            print("Successfully saved templates to JSON")

            # Verify by loading
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Verified: JSON contains {len(data)} templates")
        else:
            print("Error: Failed to save templates to JSON")

    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\nTemplate extraction test completed successfully!")
    return True


if __name__ == "__main__":
    main()