from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
import cv2
import pytesseract
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os
import base64
from io import BytesIO
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
try:
    gemini_model = genai.GenerativeModel('gemini-1.5-pro')
    logging.info("Gemini model initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Gemini model: {e}")
    gemini_model = None

EXPENSE_CSV = r"C:\Users\ARJUN K\OneDrive\Desktop\Ai finance mangement\data\expenses.csv"
if not os.path.exists(EXPENSE_CSV):
    pd.DataFrame(columns=['amount', 'merchant', 'description', 'category']).to_csv(EXPENSE_CSV, index=False)

def extract_receipt_data(text):
    amount_match = re.search(r'(?:Total|Amount|Due|Price|Bill|Rs)\s*[\$₹]?(\d{1,5}(?:[,.]\d{0,3})?)', text, re.IGNORECASE)
    amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0
    
    if amount == 0.0:
        number_matches = re.finditer(r'(\d{1,5}(?:[,.]\d{0,3})?)', text)
        candidates = [(float(m.group(1).replace(',', '')), 1.0) for m in number_matches if not any(k in text[m.start()-5:m.end()+5].lower() for k in ['hours', 'am', 'pm', 'time'])]
        amount = max(candidates, key=lambda x: x[1], default=(0.0, 0.0))[0] if candidates else 0.0
    
    lines = [line.strip() for line in text.split('\n') if line.strip() and re.search(r'[A-Za-z]', line)]
    merchant = lines[0][:50] if lines and re.search(r'[A-Za-z]', lines[0]) else "Unknown Merchant"
    description = ' '.join([l for l in lines[1:3] if re.search(r'[A-Za-z]', l) and len(l) > 3])[:100] or "No description"
    if not merchant or merchant == "Unknown Merchant":
        merchant = "Unrecognized Merchant"
    if not description or description == "No description":
        description = "Unrecognized Item"
    return {'amount': amount, 'merchant': merchant, 'description': description}

def predict_category(description, merchant):
    description = str(description).lower().strip()
    merchant = str(merchant).lower().strip()
    
    if not description and not merchant:
        logging.warning("Predict category called with empty description and merchant.")
        return 'unknown'
    description = description or "not specified"
    merchant = merchant or "unknown merchant"
    
    keyword_matches = {}
    if any(k in description for k in ['tea', 'coffee', 'latte', 'chicken', 'food', 'egg', 'burger', 'pizza', 'meal', 'snack', 'dinner', 'dosha', 'roast', 'shawarma', 'sugar']) or \
       any(k in merchant for k in ['cafe', 'restaurant', 'bakery', 'diner', 'kitchen', 'teashop']):
        keyword_matches['food'] = True
    if any(k in description for k in ['petrol', 'fuel', 'parking', 'taxi', 'bus', 'train', 'vehicle', 'car', 'bike', 'travel', 'ride']) or \
       any(k in merchant for k in ['fuel', 'gas', 'parking', 'station', 'transport', 'shell']):
        keyword_matches['transport'] = True
    if any(k in description for k in ['gadget', 'mobile', 'laptop', 'phone', 'tablet', 'computer', 'software', 'speaker']) or \
       any(k in merchant for k in ['best buy', 'amazon', 'tech', 'electronics']):
        keyword_matches['technology'] = True
    if any(k in description for k in ['groceries', 'clothing', 'shoes', 'gift', 'accessories', 'retail']) or \
       any(k in merchant for k in ['market', 'store', 'mall', 'hypermarket', 'walmart']):
        keyword_matches['shopping'] = True
    if any(k in description for k in ['movie', 'concert', 'game', 'event', 'ticket']) or \
       any(k in merchant for k in ['cinema', 'theater', 'cineplex']):
        keyword_matches['entertainment'] = True
    
    logging.info(f"Input - Description: {description}, Merchant: {merchant}, Keyword matches: {list(keyword_matches.keys())}")
    
    if len(keyword_matches) == 1:
        return list(keyword_matches.keys())[0]
    
    if not gemini_model:
        logging.warning("Gemini model unavailable, using keyword fallback.")
        if 'food' in keyword_matches:
            return 'food'
        if 'transport' in keyword_matches:
            return 'transport'
        if 'technology' in keyword_matches:
            return 'technology'
        if 'entertainment' in keyword_matches:
            return 'entertainment'
        if 'shopping' in keyword_matches:
            return 'shopping'
        return 'unknown'
    
    prompt = (
        f"Classify this expense into ONLY ONE of the following exact categories: food, transport, shopping, entertainment, technology.\n"
        f"Merchant: {merchant}\n"
        f"Description: {description}\n"
        f"Possible categories based on keywords: {', '.join(keyword_matches.keys()) if keyword_matches else 'none'}.\n"
        f"Category definitions:\n"
        f"- food: dining, groceries, snacks (e.g., coffee, meal, restaurant)\n"
        f"- transport: travel, fuel, vehicles (e.g., fuel, taxi, uber)\n"
        f"- technology: gadgets, electronics (e.g., laptop, amazon)\n"
        f"- shopping: retail, general purchases (e.g., groceries, clothing, walmart)\n"
        f"- entertainment: events, media (e.g., movie, ticket, cineplex)\n"
        f"Rules:\n"
        f"1. If keyword matches are provided, prioritize them unless context strongly contradicts.\n"
        f"2. If multiple categories match, choose the most specific or dominant context.\n"
        f"3. If no keywords match, use context alone.\n"
        f"Return ONLY the category name."
    )
    
    try:
        response = gemini_model.generate_content(prompt)
        if not response.parts:
            logging.warning(f"Gemini returned no parts. Falling back to keywords.")
            if 'food' in keyword_matches:
                return 'food'
            if 'transport' in keyword_matches:
                return 'transport'
            if 'technology' in keyword_matches:
                return 'technology'
            if 'entertainment' in keyword_matches:
                return 'entertainment'
            if 'shopping' in keyword_matches:
                return 'shopping'
            return 'unknown'
        
        predicted_category = response.text.strip().lower()
        valid_categories = ['food', 'transport', 'shopping', 'entertainment', 'technology']
        if predicted_category in valid_categories:
            return predicted_category
        else:
            logging.warning(f"Invalid category '{predicted_category}'. Falling back to keywords.")
            if 'food' in keyword_matches:
                return 'food'
            if 'transport' in keyword_matches:
                return 'transport'
            if 'technology' in keyword_matches:
                return 'technology'
            if 'entertainment' in keyword_matches:
                return 'entertainment'
            if 'shopping' in keyword_matches:
                return 'shopping'
            return 'unknown'
    
    except Exception as e:
        logging.error(f"API error: {str(e)} for Description: {description}, Merchant: {merchant}")
        if 'food' in keyword_matches:
            return 'food'
        if 'transport' in keyword_matches:
            return 'transport'
        if 'technology' in keyword_matches:
            return 'technology'
        if 'entertainment' in keyword_matches:
            return 'entertainment'
        if 'shopping' in keyword_matches:
            return 'shopping'
        return 'unknown'

def generate_recommendations():
    df = pd.read_csv(EXPENSE_CSV)
    if df.empty:
        return ["No expenses recorded. Add some to get personalized tips."]
    return ["Recommendations disabled due to API quota limits."]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/classify', methods=['POST'])
def classify():
    data = request.get_json()
    amount, merchant, description = data['amount'], data['merchant'], data['description']
    category = predict_category(description, merchant)
    return jsonify({'amount': float(amount), 'merchant': merchant, 'description': description, 'category': category})

@app.route('/api/classify_image', methods=['POST'])
def classify_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    image_file = request.files['image']
    # Read image in color
    img = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    # Adaptive thresholding for varying lighting
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # Resize to improve OCR
    thresh = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Extract text with multiple PSM settings
    text_psm6 = pytesseract.image_to_string(thresh, lang='eng', config='--psm 6')
    text_psm11 = pytesseract.image_to_string(thresh, lang='eng', config='--psm 11')
    text = text_psm6 if 'STAND FEE' in text_psm6 else text_psm11  # Prefer PSM 6 if key text is found
    
    # Debug: Encode intermediate image
    _, img_encoded = cv2.imencode('.jpg', thresh)
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')
    
    # Extract data from text
    data = extract_receipt_data(text)
    data['category'] = predict_category(data['description'], data['merchant'])
    data['raw_text'] = text
    data['debug_image'] = img_base64  # Return processed image for debugging
    return jsonify(data)

@app.route('/api/save_expense', methods=['POST'])
def save_expense():
    data = request.get_json()
    expense = {
        'amount': float(data['amount']),
        'merchant': data['merchant'],
        'description': data['description'],
        'category': data['category']
    }
    df = pd.read_csv(EXPENSE_CSV)
    df = pd.concat([df, pd.DataFrame([expense])], ignore_index=True)
    df.to_csv(EXPENSE_CSV, index=False)
    return jsonify({'status': 'success'})

@app.route('/api/get_expenses', methods=['GET'])
def get_expenses():
    df = pd.read_csv(EXPENSE_CSV)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/recommendations', methods=['GET'])
def recommendations():
    tips = generate_recommendations()
    return jsonify({'recommendations': tips})

if __name__ == '__main__':
    app.run(debug=True, port=5000)