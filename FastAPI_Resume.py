import pickle
from utils import *
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# Set Resume Request Model
class ResumeRequest(BaseModel):
    resume_text: str

# Initialize FastAPI app
app = FastAPI()

# Load the pre-trained model and TF-IDF vectorizer
pred_model = pickle.load(open('clf.pkl', 'rb'))
tfidf = pickle.load(open('tfidf.pkl', 'rb'))
label_encoder = pickle.load(open('encoder.pkl', 'rb'))

# Prediction Route to Prediction Function
@app.post('/predict')
def predict_category(req: ResumeRequest):
    try:
        cleaned_text = cleanResume(req.resume_text)
        vectorized_text = tfidf.transform([cleaned_text]).toarray()
        pred_label = pred_model.predict(vectorized_text)
        pred_category = label_encoder.inverse_transform(pred_label)
        return {"Predicted Category": pred_category[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Root Route
@app.get('/')
def root_greeting():
    return {"message": "Welcome to the Resume Category Prediction API use the /predict endpoint to get the predictions."}