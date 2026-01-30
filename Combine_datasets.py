"""
Complete Dataset Combiner
Combines 6 different resume datasets with multiple formats into a single CSV

Datasets:
- Dataset1: CSV with (Category, Resume) format
- Dataset2: CSV with (Resume, Label) format
- Dataset3-6: Folder structures with category subfolders containing files
  Supported file formats: PDF, DOCX, PNG, JPG, WEBP
"""

import os
import re
import PyPDF2
import logging
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from docx import Document
from typing import List, Tuple, Dict
from PIL import Image
import io

import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
file_handler = logging.FileHandler('Combine_datasets.log')
file_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Debug output folder for extracted text
DEBUG_TEXT_DIR = Path("logs") / "extracted_text"
DEBUG_TEXT_DIR.mkdir(parents=True, exist_ok=True)

# Suppress verbose transformers/huggingface logging
logging.getLogger('transformers').setLevel(logging.ERROR)
logging.getLogger('huggingface_hub').setLevel(logging.ERROR)

# ============================================================================
# FILE PATHS
# ============================================================================

Dataset1 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/Resume_DataSet.csv"
Dataset2 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/ResumeDataset/archive/data.csv"
Dataset3 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/ResumeDataset/archive1"
Dataset4 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/ResumeDataset/archive2/Bing_images"
Dataset5 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/ResumeDataset/archive2/resume_database"
Dataset6 = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/ResumeDataset/archive2/Scrapped_Resumes"
# Dataset1: CSV with (Category, Resume)
# Dataset2: CSV with (Resume, Label)
# Dataset3-6: Folders with Category subfolders containing files (pdf, docx, png, jpg, webp)

OUTPUT_FILE = r"/mnt/d/Beyond_College/GITHUB/Resume_Screener_Basic/Combined_Resume_Dataset.csv"

# ============================================================================
# TEXT EXTRACTION FUNCTIONS
# ============================================================================

def save_extracted_text(file_path: str, text: str, debug_name: str | None = None) -> None:
    """Save extracted text to debug folder using the source filename."""
    if not text:
        return
    try:
        src_path = Path(file_path)
        name_source = Path(debug_name) if debug_name else src_path
        safe_name = name_source.stem or "extracted"
        ext = name_source.suffix.lower().lstrip('.') or "file"
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        debug_file = DEBUG_TEXT_DIR / f"{safe_name}_{ext}_{timestamp}.txt"
        debug_file.write_text(text, encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to save extracted text for {file_path}: {e}")

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF files"""
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        text = text.strip()
        save_extracted_text(file_path, text)
        return text
    except Exception as e:
        logger.error(f"Could not extract text from PDF: {file_path} ({e})")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX files"""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        text = text.strip()
        save_extracted_text(file_path, text)
        return text
    except Exception as e:
        logger.error(f"Error extracting DOCX {file_path}: {e}")
        return ""

def extract_text_from_image(file_path: str) -> str:
    """Extract text from images using OCR API service"""
    try:
        import requests
        
        file_ext = Path(file_path).suffix.lower()
        
        # Map extensions to content types
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }

        if file_ext == '.gif':
            logger.debug(f"Converting GIF to JPG for OCR: {file_path}")
            with Image.open(file_path) as img:
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                else:
                    img = img.convert("RGB")
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                buffer.seek(0)

                logger.debug("Sending converted JPG to OCR API")
                files = {'file': (f"{Path(file_path).stem}.jpg", buffer, 'image/jpeg')}
                response = requests.post('http://localhost:8001/ocr', files=files, timeout=60)
        else:
            content_type = content_type_map.get(file_ext, 'image/png')
            logger.debug(f"Sending image {file_path} with content-type: {content_type}")
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, content_type)}
                response = requests.post('http://localhost:8001/ocr', files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                text = result.get('text', '').strip()
                save_extracted_text(file_path, text, debug_name=Path(file_path).name)
                return text
        else:
            logger.warning(f"OCR API error {response.status_code} for {file_path}: {response.text}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"OCR API not available at http://localhost:8001")
    except Exception as e:
        logger.warning(f"Error calling OCR API for {file_path}: {e}")
        import traceback
        logger.debug(traceback.format_exc())

    return ""


def extract_text_from_file(file_path: str) -> str:
    """Intelligently extract text based on file extension"""
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == '.docx':
        return extract_text_from_docx(file_path)
    elif file_ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
        return extract_text_from_image(file_path)
    else:
        logger.warning(f"Unsupported file format: {file_ext}")
        return ""

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_dataset1() -> List[Tuple[str, str]]:
    """Load Dataset1: CSV with (Category, Resume) format"""
    logger.info(f"Loading Dataset1 from {Dataset1}...")
    data = []
    try:
        df = pd.read_csv(Dataset1)
        
        for idx, row in df.iterrows():
            category = str(row['Category']).strip()
            resume = str(row['Resume']).strip()
            if category and resume:
                data.append((category, resume))
        
        logger.info(f"✓ Dataset1: Loaded {len(data)} records")
    except Exception as e:
        logger.error(f"Error loading Dataset1: {e}")
    
    return data

def load_dataset2() -> List[Tuple[str, str]]:
    """Load Dataset2: CSV with (Resume, Label) format"""
    logger.info(f"Loading Dataset2 from {Dataset2}...")
    data = []
    try:
        df = pd.read_csv(Dataset2)
            
        for idx, row in df.iterrows():
            resume = str(row['Resume']).strip()
            label = str(row['Label']).strip()
            if resume and label:
                data.append((label, resume))
        
        logger.info(f"✓ Dataset2: Loaded {len(data)} records")
    except Exception as e:
        logger.error(f"Error loading Dataset2: {e}")
    
    return data

def load_dataset_from_folders(dataset_path: str, dataset_name: str) -> List[Tuple[str, str]]:
    """Load dataset from folder structure where subfolders are categories"""
    logger.info(f"Loading {dataset_name} from {dataset_path}...")
    data = []
    
    if not os.path.exists(dataset_path):
        logger.error(f"{dataset_name} path does not exist: {dataset_path}")
        return data
    
    # Get all category folders
    category_folders = [d for d in os.listdir(dataset_path) 
                       if os.path.isdir(os.path.join(dataset_path, d))]
    
    logger.info(f"Found {len(category_folders)} categories")
    
    for category in tqdm(category_folders, desc=dataset_name):
        category_path = os.path.join(dataset_path, category)
        
        # Get all files in category folder
        try:
            files = [f for f in os.listdir(category_path) 
                    if os.path.isfile(os.path.join(category_path, f))]
        except PermissionError:
            logger.warning(f"Permission denied for {category_path}")
            continue
        
        for file in tqdm(files, desc=f"  {category}", leave=False):
            file_path = os.path.join(category_path, file)
            
            # Skip certain files
            if file.startswith('.'):
                continue
            
            # Extract text based on file type
            text = extract_text_from_file(file_path)
            
            if text and len(text) > 50:  # Only keep non-empty extractions
                data.append((category, text))
            else:
                logger.debug(f"Skipped or failed to extract: {file}")
    
    logger.info(f"✓ {dataset_name}: Loaded {len(data)} records")
    return data

def load_dataset3() -> List[Tuple[str, str]]:
    """Load Dataset3: archive1 folder structure"""
    return load_dataset_from_folders(Dataset3, "Dataset3 (archive1)")

def load_dataset4() -> List[Tuple[str, str]]:
    """Load Dataset4: archive2/Bing_images folder structure"""
    return load_dataset_from_folders(Dataset4, "Dataset4 (Bing_images)")

def load_dataset5() -> List[Tuple[str, str]]:
    """Load Dataset5: archive2/resume_database folder structure"""
    return load_dataset_from_folders(Dataset5, "Dataset5 (resume_database)")

def load_dataset6() -> List[Tuple[str, str]]:
    """Load Dataset6: archive2/Scrapped_Resumes folder structure"""
    return load_dataset_from_folders(Dataset6, "Dataset6 (Scrapped_Resumes)")

# ============================================================================
# TEXT CLEANING
# ============================================================================

def clean_text(text: str) -> str:
    """Clean and normalize resume text"""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove special control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

# ============================================================================
# MAIN COMBINING FUNCTION
# ============================================================================

def combine_all_datasets() -> pd.DataFrame:
    """Combine all 6 datasets into a single dataframe"""
    
    logger.info("="*80)
    logger.info("STARTING DATASET COMBINATION")
    logger.info("="*80)
    
    all_data = []
    
    # Load all datasets
    logger.info("\n" + "="*80)
    logger.info("LOADING DATASETS")
    logger.info("="*80 + "\n")
    
    # Dataset 1
    data1 = load_dataset1()
    all_data.extend(data1)
    
    # Dataset 2
    data2 = load_dataset2()
    all_data.extend(data2)
    
    # Dataset 3
    data3 = load_dataset3()
    all_data.extend(data3)
    
    # Dataset 4
    data4 = load_dataset4()
    all_data.extend(data4)
    
    # Dataset 5
    data5 = load_dataset5()
    all_data.extend(data5)
    
    # Dataset 6
    data6 = load_dataset6()
    all_data.extend(data6)
    
    # Create DataFrame
    logger.info("\n" + "="*80)
    logger.info("CREATING DATAFRAME")
    logger.info("="*80)
    
    df = pd.DataFrame(all_data, columns=['Category', 'Resume'])

    # Split comma-separated categories into separate rows
    logger.info("Splitting multi-label categories into separate rows...")
    df['Category'] = df['Category'].astype(str).str.split(',')
    df = df.explode('Category')
    df['Category'] = df['Category'].astype(str).str.strip()
    
    # Clean resume text
    logger.info("\nCleaning resume text...")
    df['Resume'] = df['Resume'].apply(clean_text)
    
    # Remove duplicates
    logger.info("Removing duplicates...")
    initial_count = len(df)
    df = df.drop_duplicates(subset=['Resume'], keep='first')
    duplicates_removed = initial_count - len(df)
    
    # Remove empty records
    df = df[(df['Resume'].str.len() > 50) & (df['Category'].str.len() > 0)]
    
    logger.info(f"\n" + "="*80)
    logger.info("FINAL STATISTICS")
    logger.info("="*80)
    logger.info(f"Total records extracted from datasets: {len(all_data)}")
    logger.info(f"Duplicates removed: {duplicates_removed}")
    logger.info(f"Final CSV rows: {len(df)}")
    logger.info(f"Unique categories: {df['Category'].nunique()}")
    logger.info(f"\nOutput file: {OUTPUT_FILE}")
    logger.info(f"\nCategory distribution:")
    
    category_counts = df['Category'].value_counts()
    for category, count in category_counts.items():
        logger.info(f"  {category}: {count}")
    
    return df

# ============================================================================
# SAVING FUNCTION
# ============================================================================

def save_dataset(df: pd.DataFrame, output_path: str = OUTPUT_FILE) -> bool:
    """Save combined dataset to CSV"""
    try:
        logger.info(f"\n" + "="*80)
        logger.info("SAVING DATASET")
        logger.info("="*80)
        logger.info(f"Saving to: {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"✓ Dataset saved successfully!")
        logger.info(f"  File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
        logger.info(f"  Rows: {len(df)}")
        logger.info(f"  Columns: {len(df.columns)}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving dataset: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        # Combine all datasets
        combined_df = combine_all_datasets()
        
        # Save to CSV
        success = save_dataset(combined_df)
        
        if success:
            logger.info("\n" + "="*80)
            logger.info("✅ DATASET COMBINATION COMPLETED SUCCESSFULLY!")
            logger.info("="*80)
            
            # Display preview
            logger.info("\nDataset Preview (first 5 rows):")
            logger.info("\n" + str(combined_df.head()))
            
        else:
            logger.error("\n❌ Failed to save dataset")
    
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()