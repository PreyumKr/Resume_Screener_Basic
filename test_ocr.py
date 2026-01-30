"""
Test script for OCR service
Tests the Pytesseract-based OCR API
"""
import requests
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OCR_SERVICE_URL = "http://localhost:8001/ocr"
HEALTH_CHECK_URL = "http://localhost:8001/health"
TEST_IMAGE = "/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/Preview.png"

def test_health_check():
    """Test if OCR service is healthy"""
    try:
        logger.info("Checking OCR service health...")
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Health check passed: {data.get('message')}")
            return True
        else:
            logger.error(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to OCR service. Is it running on port 8001?")
        return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

def test_ocr_extraction(image_path: str):
    """
    Test OCR text extraction from image
    
    Args:
        image_path: Path to image file
    """
    try:
        # Check if file exists
        if not Path(image_path).exists():
            logger.error(f"❌ Image file not found: {image_path}")
            return None
        
        # Get file size
        file_size = Path(image_path).stat().st_size
        logger.info(f"File size: {file_size} bytes")
        
        # Open and send image
        logger.info(f"Sending image to {OCR_SERVICE_URL}...")
        with open(image_path, 'rb') as img_file:
            files = {'file': (Path(image_path).name, img_file, 'image/png')}
            response = requests.post(OCR_SERVICE_URL, files=files, timeout=60)
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            logger.info("[OK] OCR extraction successful!")
            
            extracted_text = data.get('text', '')
            
            logger.info("\n" + "="*80)
            logger.info("EXTRACTED TEXT:")
            logger.info("="*80)
            print(extracted_text)
            logger.info("\n" + "="*80)
            
            logger.info(f"\n[SUCCESS] OCR test completed successfully!")
            return extracted_text
        else:
            logger.error(f"❌ OCR failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out. Image processing took too long.")
        return None
    except Exception as e:
        logger.error(f"❌ OCR extraction error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Check if image path provided as argument
    if len(sys.argv) > 1:
        test_image_path = sys.argv[1]
    else:
        test_image_path = TEST_IMAGE
    
    # Check if file exists
    if not Path(test_image_path).exists():
        logger.error(f"❌ Test image not found: {test_image_path}")
        logger.info(f"Usage: python {Path(__file__).name} <image_path>")
        logger.info(f"Example: python {Path(__file__).name} test_image.png")
        sys.exit(1)
    
    logger.info("="*80)
    logger.info("🧪 Testing Pytesseract OCR Service")
    logger.info("="*80)
    
    # Step 1: Health check
    if not test_health_check():
        logger.error("\n❌ OCR service is not available. Please start it first:")
        logger.error("   python ocr_service.py")
        sys.exit(1)
    
    # Step 2: Test OCR
    logger.info("\n📷 Testing OCR extraction:")
    logger.info("-"*80)
    result = test_ocr_extraction(test_image_path)
    
    if result is not None:
        logger.info("\n✨ All tests passed!")
    else:
        logger.error("\n❌ OCR test failed!")
        sys.exit(1)
