from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import time
import os

from src.core.config_manager import ConfigManager
from src.llm.openrouter_client import OpenRouterClient
from src.templates.template_model import Template
from src.utils.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)


class ReportGenerator:
    """
    Generates ultrasound reports using multimodal LLM analysis.

    Implements stateful, multi-turn conversation logic:
    - Start with system prompt
    - Process images in batches (configurable, default 10)
    - Update cumulative "summary of findings"
    - Generate final report using summary and selected template
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize the ReportGenerator.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.llm_client = OpenRouterClient(
            api_key=config.llm.api_key,
            base_url=getattr(config.llm, 'base_url', "https://openrouter.ai/api/v1")
        )

        # Batch size for image processing
        self.batch_size = getattr(config.llm, 'max_images_per_request', 10)

        # System prompt for ultrasound analysis
        self.system_prompt = self._get_system_prompt()
        
        # Paths to breast-specific files
        self.breast_prompt_file = "breast_case_specific_prompt.txt"
        self.breast_few_shot_file = "breast_case_few_shot.txt"

        # Initialize persistent conversation history
        self.conversation_history = []
        
        # Counter for LLM API calls (for audit logging)
        self.llm_call_count = 0

        logger.info("ReportGenerator initialized")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for ultrasound report generation."""
        return """You are an expert radiologist analyzing ultrasound images for medical report generation.

Your task is to analyze ultrasound images and build a comprehensive summary of findings that will be used to generate a structured medical report.

For each batch of images you receive:
1. Analyze the anatomical structures, pathology, and any abnormalities visible
2. Update and maintain a cumulative "Summary of Findings" that combines information from all previous batches
3. Be specific about locations, measurements, characteristics, and clinical significance
4. Use appropriate medical terminology and standardized descriptions
5. Maintain consistency across batches - don't contradict previous findings unless new evidence suggests otherwise

When generating the final report:
- Use the provided template structure
- Fill in each section with relevant findings from your cumulative summary
- Ensure the report is comprehensive, accurate, and clinically appropriate
- Follow standard medical reporting conventions

Always prioritize patient safety and clinical accuracy in your analysis."""

    def _load_breast_specific_prompt(self) -> Optional[str]:
        """
        Load breast-specific prompt from file.
        
        Returns:
            Content of breast_case_specific_prompt.txt or None if not found
        """
        try:
            if os.path.exists(self.breast_prompt_file):
                with open(self.breast_prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Loaded breast-specific prompt from {self.breast_prompt_file}")
                return content
            else:
                logger.warning(f"Breast-specific prompt file not found: {self.breast_prompt_file}")
                return None
        except Exception as e:
            logger.error(f"Failed to load breast-specific prompt: {e}")
            return None
    
    def _load_breast_few_shot_examples(self) -> Optional[str]:
        """
        Load breast few-shot examples from file.
        
        Returns:
            Content of breast_case_few_shot.txt or None if not found
        """
        try:
            if os.path.exists(self.breast_few_shot_file):
                with open(self.breast_few_shot_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Loaded breast few-shot examples from {self.breast_few_shot_file}")
                return content
            else:
                logger.warning(f"Breast few-shot examples file not found: {self.breast_few_shot_file}")
                return None
        except Exception as e:
            logger.error(f"Failed to load breast few-shot examples: {e}")
            return None

    def _create_initial_summary(self) -> str:
        """Create initial empty summary of findings."""
        return "SUMMARY OF FINDINGS:\n\nNo images analyzed yet."

    def _update_summary_prompt(self, current_summary: str, batch_number: int, total_batches: int) -> str:
        """
        Create prompt for updating summary with new batch of images.

        Args:
            current_summary: Current cumulative summary
            batch_number: Current batch number (1-based)
            total_batches: Total number of batches

        Returns:
            Prompt for LLM to update summary
        """
        return f"""Please analyze this batch of ultrasound images (batch {batch_number} of {total_batches}) and update the cumulative Summary of Findings.

CURRENT SUMMARY OF FINDINGS:
{current_summary}

INSTRUCTIONS:
1. Analyze all images in this batch for anatomical structures, abnormalities, and clinical findings
2. Update the Summary of Findings to incorporate new information from this batch
3. Maintain all relevant findings from previous batches
4. Organize findings by anatomical region and clinical significance
5. Be specific about locations, sizes, characteristics, and implications
6. If this is the final batch, ensure the summary is complete and ready for report generation

Provide your response as an updated "SUMMARY OF FINDINGS" section only."""

    def _create_final_report_prompt(self, summary: str, template: Template, template_name: str, prior_report: Optional[str] = None) -> str:
        """
        Create prompt for generating final report using summary and template.
        Includes few-shot examples for breast cases and prior report if available.

        Args:
            summary: Final cumulative summary of findings
            template: Selected report template
            template_name: Name of the selected template
            prior_report: Optional prior report text for comparison

        Returns:
            Prompt for final report generation
        """
        template_structure = json.dumps(template.sections, indent=2)
        
        # Check if this is a breast case and load few-shot examples
        few_shot_examples = ""
        if "BREAST" in template_name.upper():
            examples = self._load_breast_few_shot_examples()
            if examples:
                few_shot_examples = f"""\n\nFEW-SHOT EXAMPLES:
Here are examples of well-formatted breast ultrasound reports for reference:

{examples}

Please follow similar formatting, structure, and clinical terminology as shown in these examples.
"""
                logger.info("Including few-shot examples in final report prompt for breast case")

        # Add prior report section if provided
        prior_report_section = ""
        prior_report_instruction = ""
        if prior_report:
            prior_report_section = f"""

---PRIOR REPORT---
{prior_report}
---END PRIOR REPORT---
"""
            prior_report_instruction = " AND the prior report provided above"
            logger.info("Including prior report in final report prompt for comparison")

        return f"""Using the cumulative Summary of Findings below, generate a complete ultrasound report following the provided template structure.{few_shot_examples}{prior_report_section}

SUMMARY OF FINDINGS:
{summary}

TEMPLATE STRUCTURE:
{template_structure}

INSTRUCTIONS:
1. Fill in each section of the template with relevant clinical information from the Summary of Findings
2. Use appropriate medical terminology and formatting
3. Ensure clinical accuracy and completeness
4. Follow standard medical reporting conventions
5. If a section has no relevant findings, indicate "No significant findings" or similar appropriate text
6. Generate a professional, comprehensive medical report
{f"7. Compare findings with the prior report and explicitly note any significant changes, new findings, or stability compared to the prior study." if prior_report else ""}

Based on the provided examples, the cumulative summary of findings, the report template{prior_report_instruction}, generate a complete, narrative clinical report.{" Explicitly note any significant changes, new findings, or stability compared to the prior study." if prior_report else ""} Your response MUST strictly follow the structure, sentence structure (e.g. if the examples wrote "Findings are likely benign and can represent mild changes of mammary duct ectasia.", reuse this sentence instead of reporting in other ways like "There is evidence of subareolar ductal ectasia."), narrative style, and formatting of the examples. Do NOT use markdown formatting like bolding ('**') for emphasis. The output should be a clean plain-text document. Do NOT return JSON format - provide only the clean narrative text report."""

    def process_images_batch(self, image_paths: List[str], current_summary: str,
                           batch_number: int, total_batches: int, template_name: str = "") -> str:
        """
        Process a batch of images and update the cumulative summary.
        Adds breast-specific prompt for breast cases on first batch.
        Uses persistent conversation history.

        Args:
            image_paths: List of paths to images in this batch
            current_summary: Current cumulative summary
            batch_number: Current batch number (1-based)
            total_batches: Total number of batches
            template_name: Name of selected template (for conditional prompting)

        Returns:
            Updated summary of findings
        """
        if not image_paths:
            logger.warning(f"Empty batch {batch_number}, returning current summary")
            return current_summary

        logger.info(f"Processing batch {batch_number}/{total_batches} with {len(image_paths)} images")

        # Create multimodal message
        prompt = self._update_summary_prompt(current_summary, batch_number, total_batches)
        message = self.llm_client.create_multimodal_message(prompt, image_paths)
        
        # Add breast-specific prompt for breast cases (only on first batch)
        if batch_number == 1 and "BREAST" in template_name.upper():
            breast_prompt = self._load_breast_specific_prompt()
            if breast_prompt:
                self.conversation_history.append({"role": "user", "content": breast_prompt})
                logger.info("Added breast-specific prompt to conversation for breast case")
        
        # Add current batch message to conversation history
        self.conversation_history.append(message)

        try:
            # Generate response using persistent conversation history
            self.llm_call_count += 1
            response = self.llm_client.generate_response(
                messages=self.conversation_history,
                model=self.config.llm.model,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )

            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})

            # Extract updated summary (should start with "SUMMARY OF FINDINGS:")
            if "SUMMARY OF FINDINGS:" in response:
                updated_summary = response.split("SUMMARY OF FINDINGS:", 1)[1].strip()
                updated_summary = f"SUMMARY OF FINDINGS:{updated_summary}"
            else:
                # Fallback: assume entire response is the updated summary
                updated_summary = response.strip()

            logger.info(f"Successfully processed batch {batch_number}")
            return updated_summary

        except Exception as e:
            logger.error(f"Failed to process batch {batch_number}: {e}")
            # Return current summary unchanged on error
            return current_summary

    def generate_report(self, image_paths: List[str], template: Template, template_name: str = "", prior_report: Optional[str] = None) -> tuple:
        """
        Generate a complete ultrasound report from images using the specified template.
        Implements stateful conversation with persistent history across all LLM calls.
        Implements conditional prompting and few-shot learning for breast cases.
        Supports prior report comparison when prior_report is provided.

        Args:
            image_paths: List of paths to processed/cleaned images
            template: Selected report template
            template_name: Name of the selected template (for conditional prompting)
            prior_report: Optional prior report text for comparison

        Returns:
            Tuple of (report_text, llm_call_count):
            - report_text: Complete report text
            - llm_call_count: Number of LLM API calls made during generation
        """
        if not image_paths:
            raise ValueError("No images provided for report generation")

        # Use template name from parameter or from template object
        if not template_name:
            template_name = template.name
            
        logger.info(f"Starting report generation with {len(image_paths)} images using template: {template_name}")

        # Reset LLM call counter for this report generation
        self.llm_call_count = 0

        # Initialize persistent conversation history with system prompt
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Split images into batches
        batches = [image_paths[i:i + self.batch_size] for i in range(0, len(image_paths), self.batch_size)]
        total_batches = len(batches)

        # Initialize summary
        current_summary = self._create_initial_summary()

        # Process each batch with template name for conditional prompting
        # Each batch appends to the persistent conversation_history
        for batch_num, batch_images in enumerate(batches, 1):
            current_summary = self.process_images_batch(
                batch_images, current_summary, batch_num, total_batches, template_name
            )

        logger.info("All image batches processed, generating final report" + (" with prior report comparison" if prior_report else ""))

        # Generate final report with few-shot learning and optional prior report
        final_prompt = self._create_final_report_prompt(current_summary, template, template_name, prior_report)
        final_message = {"role": "user", "content": final_prompt}

        # Add final prompt to persistent conversation history
        self.conversation_history.append(final_message)

        try:
            # Generate final report using complete conversation history
            self.llm_call_count += 1
            report_text = self.llm_client.generate_response(
                messages=self.conversation_history,
                model=self.config.llm.model,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )

            logger.info(f"Report generation completed successfully with {self.llm_call_count} LLM calls")
            logger.debug(f"Final conversation history had {len(self.conversation_history)} messages")
            
            return report_text, self.llm_call_count

        except Exception as e:
            logger.error(f"Failed to generate final report: {e}")
            raise

    def save_report(self, report_text: str, output_path: Path) -> None:
        """
        Save the generated report to a file.

        Args:
            report_text: Complete report text
            output_path: Path to save the report
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)

            logger.info(f"Report saved to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
            raise