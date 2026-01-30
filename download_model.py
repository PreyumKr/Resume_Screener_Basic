"""
Download and cache the DeepSeek-OCR model to ensure all custom code is available
This model depends on DeepSeek-V2, so we need to download both
"""
import torch
import os

print("Downloading DeepSeek-OCR model and dependencies...")

# Set cache location
os.environ['TRANSFORMERS_CACHE'] = os.path.expanduser('~/.cache/huggingface/hub')
os.environ['HF_DATASETS_CACHE'] = os.path.expanduser('~/.cache/huggingface/datasets')

from transformers import AutoModel, AutoTokenizer

model_name = "deepseek-ai/DeepSeek-OCR"

try:
    print("1. Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        trust_remote_code=True,
        local_files_only=False,
        force_download=False  # Use cache if available
    )
    print("   [OK] Tokenizer downloaded")
    
    print("2. Downloading model (this may take several minutes)...")
    print("   This includes DeepSeek-V2 dependencies...")
    
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        local_files_only=False,
        force_download=False,
        attn_implementation="eager",
        torch_dtype=torch.bfloat16,
        device_map="cuda:0" if torch.cuda.is_available() else "cpu"
    )
    print("   [OK] Model downloaded and loaded")
    
    # Test the infer method exists
    if hasattr(model, 'infer'):
        print("   [OK] Model has infer() method")
    
    print("\n[SUCCESS] All model files are now cached and ready!")
    print("You can now run: python ocr_service.py")
    
except Exception as e:
    print(f"\n[ERROR] Failed to download model: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Try clearing HuggingFace cache:")
    print("   - Delete: C:\\Users\\<username>\\.cache\\huggingface")
    print("3. Then run this script again")
    import traceback
    traceback.print_exc()
