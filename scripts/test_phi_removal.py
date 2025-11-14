from pathlib import Path

from src.processors.phi_remover import PhiRemover
from src.core.config_manager import ConfigManager

def main():
    config = ConfigManager()
    phi_remover = PhiRemover(config)

    input_dir = Path("temp/test_conversion_output/Us_Breast_(Bilateral) - US23__USBREAST/US_BREAST_(BILATERAL)_1")
    output_dir = Path("temp/phi_removed_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    jpg_files = list(input_dir.glob("*.jpg"))

    processed_count = 0
    for jpg_file in jpg_files:
        output_path = output_dir / jpg_file.name
        phi_remover.process_file(str(jpg_file), str(output_path))
        processed_count += 1

    print(f"Processed {processed_count} images. PHI-removed images saved in {output_dir}")

if __name__ == "__main__":
    main()