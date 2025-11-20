import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.SXPrefrontal.model import SXPrefrontalModel

def main():
    print("Initializing SXPrefrontalModel...")
    try:
        model = SXPrefrontalModel()
        
        if not model.client.is_available():
            print("Error: Qwen CLI is not available. Please install it first.")
            return

        prompt = "What is 2 + 2? Answer briefly."
        print(f"Sending prompt: '{prompt}'")
        
        response = model.generate(prompt)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
