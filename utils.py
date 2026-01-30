import re
import docx
import PyPDF2
import requests

# Function to clean resume text
def cleanResume(txt):
    # Remove URLs
    cleanText = re.sub(r'http\S+\s', ' ', txt)
    
    # Remove 'RT' and 'cc' (commonly found in retweets and mentions)
    cleanText = re.sub(r'RT|cc', ' ', cleanText)
    
    # Remove hashtags
    cleanText = re.sub(r'#\S+\s', ' ', cleanText)
    
    # Remove mentions (words starting with @)
    cleanText = re.sub(r'@\S+', '  ', cleanText)
    
    # Remove punctuation and special characters
    cleanText = re.sub(r'[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    
    # Remove non-ASCII characters
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    
    # Replace multiple spaces with a single space
    cleanText = re.sub(r'\s+', ' ', cleanText)

    return cleanText


# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text


# Function to extract text from TXT with explicit encoding handling
def extract_text_from_txt(file):
    # Try using utf-8 encoding for reading the text file
    try:
        text = file.read().decode('utf-8')
    except UnicodeDecodeError:
        # In case utf-8 fails, try 'latin-1' encoding as a fallback
        try:
            text = file.read().decode('latin-1')
        except Exception as e:
            raise ValueError(f"Error reading the text file: {str(e)}")
    return text


# Function to handle file upload and extraction
def handle_file_upload(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'pdf':
        text = extract_text_from_pdf(uploaded_file)
    elif file_extension == 'docx':
        text = extract_text_from_docx(uploaded_file)
    elif file_extension == 'txt':
        text = extract_text_from_txt(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")
    return text


# Function to get prediction from FastAPI server
def get_prediction(resume_text):
    # For Docker 
    # Fast_API_URL = "http://localhost:8000/predict"
    # For K8s
    Fast_API_URL = "http://localhost:5000/predict"
    try:
        response = requests.post(Fast_API_URL, json={"resume_text": resume_text}, timeout=60)
        if response.status_code == 200:
            return response.json().get("Predicted Category", "Not Available")
        else:
            raise ValueError(f"Error from Prediction Server: {response.status_code} - {response.text}")
    except Exception as e:
        raise ValueError(f"API Error: {str(e)}")