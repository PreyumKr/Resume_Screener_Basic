import os
import uvicorn
import logging
import sys
from pathlib import Path
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, UploadFile, HTTPException
import pytesseract
from PIL import Image
import io

# Setup logging with both console and file output
LOG_FILE = "ocr_service.log"
script_dir = Path(__file__).parent.absolute()
logs_dir = script_dir / "logs"
logs_dir.mkdir(exist_ok=True)
log_path = logs_dir / LOG_FILE
debug_dir = logs_dir / "ocr_debug"
debug_dir.mkdir(parents=True, exist_ok=True)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)


# File handler
file_handler = logging.FileHandler(str(log_path))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Log startup
logger.info(f"OCR Service logs will be saved to: {log_path.absolute()}")

app = FastAPI(title="OCR Service", description="Pytesseract OCR API for text extraction")

# Configuration
# Uncomment and set if tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def verify_tesseract():
    """Verify Tesseract is installed and accessible"""
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"[OK] Tesseract version: {version}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Tesseract not found: {e}")
        return False

@app.post("/ocr")
async def extract_text_from_image(file: UploadFile = File(...)):
    """
    Extract text from image file using Pytesseract
    
    Args:
        file: Image file (PNG, JPG, WEBP)
    
    Returns:
        JSON with extracted text
    """
    try:
        if file.content_type not in ["image/png", "image/jpeg", "image/webp", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Only PNG, JPG, WEBP images are supported")
        
        # Read image file
        content = await file.read()
        
        logger.info(f"Processing image: {file.filename}")
        
        # Open image with PIL
        image = Image.open(io.BytesIO(content))
        
        # Extract text using pytesseract
        response = pytesseract.image_to_string(image)
        
        if not response or not response.strip():
            logger.warning(f"No text extracted from {file.filename}")
            response = ""

        # Save raw response for debugging
        safe_name = Path(file.filename or "upload").stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = debug_dir / f"{safe_name}_{timestamp}.txt"
        try:
            debug_file.write_text(response, encoding="utf-8")
            logger.info(f"Saved OCR debug output to: {debug_file}")
        except Exception as e:
            logger.warning(f"Failed to save OCR debug output: {e}")
        
        logger.info(f"Successfully extracted text from {file.filename}")
        
        return JSONResponse({"text": response.strip(), "success": True})
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if verify_tesseract():
        return JSONResponse({"status": "healthy", "message": "OCR service ready"})
    else:
        return JSONResponse(
            {"status": "unhealthy", "message": "Tesseract not found"}, 
            status_code=503
        )

if __name__ == "__main__":
    logger.info("Initializing Pytesseract OCR Service...")
    
    if not verify_tesseract():
        logger.error("[FAIL] STARTUP FAILED: Tesseract not found")
        logger.error("Please install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract")
        exit(1)
    
    logger.info("[OK] Tesseract OCR ready!")

    uvicorn.run(app, host="0.0.0.0", port=8001)
