"""
Test script to verify the prompts refactoring works correctly.
"""

import sys
import os

# Add prompts folder to path
prompts_path = os.path.join(os.path.dirname(__file__), 'src', 'modules', 'SXThalamus', 'prompts')
sys.path.insert(0, prompts_path)

# Import individual prompt functions
from semantic_grouping import build_semantic_grouping_prompt
from default import build_default_prompt
from custom import build_custom_prompt

def test_prompts():
    """Test all prompt builder methods."""

    print("Testing individual prompt functions...\n")

    # Test custom prompt
    custom_result = build_custom_prompt(
        "Analyze this {content_type}: {content}",
        content_type="code",
        content="def hello(): pass"
    )
    assert "code" in custom_result
    assert "def hello(): pass" in custom_result
    print("[OK] build_custom_prompt works")

    # Test default prompt
    default_result = build_default_prompt("test message")
    assert "test message" in default_result
    assert len(default_result) > 0
    print("[OK] build_default_prompt works")

    # Test semantic grouping prompt
    semantic_result = build_semantic_grouping_prompt("user: hello\nassistant: hi there")
    assert "user: hello" in semantic_result
    assert len(semantic_result) > 100  # Should be a long prompt
    print("[OK] build_semantic_grouping_prompt works")

    print("\n[SUCCESS] All prompt functions work correctly!")
    print(f"\nPrompt files structure:")
    print("  src/modules/SXThalamus/prompts/")
    print("  |-- __init__.py          (exports all functions)")
    print("  |-- semantic_grouping.py (main semantic grouping prompt)")
    print("  |-- default.py           (legacy default prompt)")
    print("  +-- custom.py            (template-based custom prompt)")
    print("\nOrchestrator:")
    print("  src/modules/SXThalamus/prompts.py")
    print("  +-- SXThalamusPromptBuilder (delegates to prompt functions)")
    print("\n[SUCCESS] Refactoring complete!")
    print("   Each prompt is now in its own file for easy maintenance.")
    print("   The SXThalamusPromptBuilder acts as a loader/orchestrator.")

if __name__ == "__main__":
    test_prompts()
