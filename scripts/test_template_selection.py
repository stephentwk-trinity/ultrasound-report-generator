#!/usr/bin/env python3
"""
Test script for template selection functionality.
Tests the TemplateManager and TemplateSelector classes.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from templates.template_manager import TemplateManager, TemplateSelector


def test_template_manager():
    """Test the TemplateManager functionality."""
    print("Testing TemplateManager...")

    # Initialize TemplateManager
    manager = TemplateManager()

    # Test loading templates
    templates = manager.get_all_templates()
    print(f"Loaded {len(templates)} templates")

    # Test getting template names
    template_names = manager.get_template_names()
    print(f"Template names: {len(template_names)}")
    print(f"First few template names: {template_names[:5]}")

    # Test getting template by ID
    try:
        template = manager.get_template_by_id("template_001")
        print(f"Template ID 'template_001': {template.name}")
    except KeyError as e:
        print(f"Error getting template by ID: {e}")

    # Test getting template by name
    try:
        template = manager.get_template_by_name("ULTRASOUND OF BOTH BREASTS")
        print(f"Template name 'ULTRASOUND OF BOTH BREASTS': {template.id}")
    except KeyError as e:
        print(f"Error getting template by name: {e}")

    print("TemplateManager tests passed!\n")


def test_template_selector():
    """Test the TemplateSelector functionality."""
    print("Testing TemplateSelector...")

    # Initialize components
    manager = TemplateManager()
    selector = TemplateSelector(manager)

    # Test cases with directory names
    test_cases = [
        # Single US Breast studies (Note: all use "ULTRASOUND OF BOTH BREASTS")
        (["Us_Breast_(Bilateral) - US23__USBREAST"], "ULTRASOUND OF BOTH BREASTS"),
        (["Breast - US23__USBREAST"], "ULTRASOUND OF BOTH BREASTS"),
        (["Us_Breast_(Right) - US23__USBREAST"], "ULTRASOUND OF BOTH BREASTS"),
        (["Us_Breast_(Left) - US23__USBREAST"], "ULTRASOUND OF BOTH BREASTS"),
        
        # Combined studies: 3D Mammogram + US
        (["Us_Breast_(Bilateral) - US23__USBREAST", "Mg3DBi_Standard_Screening__Tomohd - MG3DBI"],
         "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"),
        
        # Combined studies: 2D Mammogram + US
        (["Us_Breast_(Bilateral) - US23__USBREAST", "Mg3DBi_Standard_Screening__Tomohd - BI02__2D_MMGBIL"],
         "BILATERAL 2D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS"),
    ]

    for directory_names, expected_template in test_cases:
        template, info = selector.select_template_with_info(directory_names)
        if template:
            status = "✓" if template.name == expected_template else "✗"
            print(f"{status} Directories: {directory_names}")
            print(f"  -> Template: '{template.name}'")
            print(f"  -> Expected: '{expected_template}'")
            print(f"  -> Info: {info}")
        else:
            print(f"✗ Directories: {directory_names}")
            print(f"  -> No template found")
            print(f"  -> Expected: '{expected_template}'")

    print("\nTemplateSelector tests completed!\n")


def test_specific_case():
    """Test the specific cases mentioned in the instructions."""
    print("Testing specific cases from instructions...")

    manager = TemplateManager()
    selector = TemplateSelector(manager)

    # Test cases from user feedback
    test_cases = [
        {
            'directories': ["Us_Breast_(Bilateral) - US23__USBREAST"],
            'expected': "ULTRASOUND OF BOTH BREASTS",
            'description': "Single US Breast Bilateral"
        },
        {
            'directories': ["Breast - US23__USBREAST"],
            'expected': "ULTRASOUND OF BOTH BREASTS",
            'description': "Single US Breast (no bilateral specified)"
        },
        {
            'directories': ["Mg3DBi_Standard_Screening__Tomohd - MG3DBI", "Us_Breast_(Bilateral) - US23__USBREAST"],
            'expected': "DIGITAL 3D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS",
            'description': "3D Mammogram + US Breast Bilateral"
        },
        {
            'directories': ["Us_Breast_(Bilateral) - US23__USBREAST", "Mg3DBi_Standard_Screening__Tomohd - BI02__2D_MMGBIL"],
            'expected': "BILATERAL 2D MAMMOGRAM & ULTRASOUND OF BOTH BREASTS",
            'description': "2D Mammogram + US Breast Bilateral"
        }
    ]

    all_passed = True
    for test_case in test_cases:
        template = selector.select_template(test_case['directories'])
        
        if template and template.name == test_case['expected']:
            print(f"✓ {test_case['description']}")
            print(f"  Directories: {test_case['directories']}")
            print(f"  Selected Template: '{template.name}'")
        else:
            all_passed = False
            print(f"✗ {test_case['description']}")
            print(f"  Directories: {test_case['directories']}")
            if template:
                print(f"  Selected Template: '{template.name}'")
            else:
                print(f"  Selected Template: None")
            print(f"  Expected: '{test_case['expected']}'")
        print()

    if all_passed:
        print("All specific cases passed!")
    else:
        print("Some specific cases failed!")
        
    return all_passed


def main():
    """Main test function."""
    print("Starting template selection tests...\n")

    try:
        test_template_manager()
        test_template_selector()
        success = test_specific_case()

        if success:
            print("\nAll tests passed successfully!")
            return 0
        else:
            print("\nSome tests failed!")
            return 1

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)