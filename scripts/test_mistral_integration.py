"""
Test script to verify Mistral integration with ICMs.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_mistral_client():
    """Test basic Mistral client functionality."""
    print("=" * 60)
    print("TEST 1: Mistral Client")
    print("=" * 60)
    
    from src.modules.llm.mistral_sdk.client import MistralClient
    
    try:
        client = MistralClient(model="mistral-medium-2508")
        response = await client.generate_content("What is 2+2? Answer in one word.")
        print(f"✓ Mistral client works")
        print(f"  Response: {response[:100]}")
    except Exception as e:
        print(f"✗ Mistral client failed: {e}")
        return False
    
    return True


async def test_llm_service():
    """Test LLMService with Mistral."""
    print("\n" + "=" * 60)
    print("TEST 2: LLMService with Mistral")
    print("=" * 60)
    
    from src.modules.llm import LLMService
    from src.database import DatabaseManager
    
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        llm_service = LLMService(db_manager=db_manager)
        
        # This would require a user with mistral model configured
        # For now, just verify the service can be instantiated
        print(f"✓ LLMService instantiated successfully")
        
        await db_manager.close()
    except Exception as e:
        print(f"✗ LLMService test failed: {e}")
        return False
    
    return True


def test_sxprefrontal_model():
    """Test SXPrefrontalModel with different providers."""
    print("\n" + "=" * 60)
    print("TEST 3: SXPrefrontalModel Multi-Provider")
    print("=" * 60)
    
    from src.modules.SXPrefrontal import SXPrefrontalModel
    
    # Test Qwen (default)
    try:
        model_qwen = SXPrefrontalModel(provider="qwen")
        print(f"✓ SXPrefrontalModel (Qwen) instantiated")
    except Exception as e:
        print(f"✗ Qwen provider failed: {e}")
        return False
    
    # Test Mistral
    try:
        model_mistral = SXPrefrontalModel(provider="mistral", model="mistral-medium-2508")
        print(f"✓ SXPrefrontalModel (Mistral) instantiated")
    except Exception as e:
        print(f"✗ Mistral provider failed: {e}")
        return False
    
    # Test Gemini
    try:
        model_gemini = SXPrefrontalModel(provider="gemini", model="gemini-2.0-flash")
        print(f"✓ SXPrefrontalModel (Gemini) instantiated")
    except Exception as e:
        print(f"✗ Gemini provider failed: {e}")
        return False
    
    return True


def test_user_config_service():
    """Test UserConfigService ICM configuration."""
    print("\n" + "=" * 60)
    print("TEST 4: UserConfigService ICM Config")
    print("=" * 60)
    
    from src.services.user_config_service import UserConfigService
    
    try:
        service = UserConfigService()
        
        # Get default config
        config = service._get_default_config()
        
        # Test ICM config extraction
        intent_config = service.get_icm_config(config, "intent_icm")
        time_config = service.get_icm_config(config, "time_icm")
        world_view_config = service.get_icm_config(config, "world_view_icm")
        
        print(f"✓ Intent ICM config: {intent_config}")
        print(f"✓ Time ICM config: {time_config}")
        print(f"✓ World View ICM config: {world_view_config}")
        
        assert intent_config["provider"] == "qwen"
        assert time_config["provider"] == "qwen"
        assert world_view_config["provider"] == "google"
        
        print(f"✓ All ICM configs valid")
    except Exception as e:
        print(f"✗ UserConfigService test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("\n🚀 Starting Mistral Integration Verification\n")
    
    results = []
    
    # Run tests
    results.append(await test_mistral_client())
    results.append(await test_llm_service())
    results.append(test_sxprefrontal_model())
    results.append(test_user_config_service())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
