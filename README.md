# AI Finance Management

## Overview

AI Finance Management is a web application designed to help users track and categorize their expenses. It uses OCR to extract data from receipts and classifies expenses into categories (e.g., food, transport, shopping) using keyword-based logic. The application is built with Flask and supports manual expense entry as well as image-based receipt processing.

## Features

- **Expense Classification**: Automatically categorizes expenses into predefined categories (`food`, `transport`, `shopping`, `entertainment`, `technology`) using keyword-based rules.
- **Receipt OCR**: Extracts data (amount, merchant, description) from receipt images using Tesseract OCR.
- **Manual Entry**: Allows users to manually input expenses via a web interface.
- **Expense Tracking**: Stores expenses in a CSV file and provides an API to retrieve them.
- **Debugging Support**: Logs detailed information for debugging, including OCR results and classification decisions.
- **Extensible**: Includes optional integration with the Gemini API for advanced expense classification (currently disabled due to quota limits).

## Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed on your system
  - Windows: Download and install from the official Tesseract website. Ensure `tesseract.exe` is in `C:\Program Files\Tesseract-OCR\`.
  - Linux: Install via `sudo apt-get install tesseract-ocr`.
  - macOS: Install via `brew install tesseract`.
- A virtual environment (recommended)

## Setup

### Clone the Project

Ensure you have the project files in a directory, e.g., `ai-finance-management/`.

### Set Up a Virtual Environment

```bash
cd ai-finance-management
python -m venv ai_finance
```

Activate the virtual environment:
- Windows: `ai_finance\Scripts\activate`
- Linux/macOS: `source ai_finance/bin/activate`

### Install Dependencies

Install the required Python packages:

```bash
pip install flask pandas numpy opencv-python pytesseract google-generative-ai python-dotenv
```

### Configure Tesseract

Ensure the Tesseract path in `src/app.py` matches your installation:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update for your OS
```

### Set Up Environment Variables

Create a `.env` file in the project root:

```plaintext
GEMINI_API_KEY=your_gemini_api_key_here
```

Note: The Gemini API is currently disabled due to quota limits. You can skip this step for now.

## Directory Structure

```
ai-finance-management/
├── data/
│   └── expenses.csv         # Stores expense records
├── src/
│   ├── app.py              # Main Flask application
│   ├── static/
│   │   └── js/
│   │       └── script.js   # Frontend JavaScript
│   └── templates/
│       └── index.html      # HTML template for the web interface
├── .env                    # Environment variables
└── README.md
```

## Usage

### Run the Application

```bash
cd src
python app.py
```

- The app will start a development server at `http://127.0.0.1:5000/`.
- Debug mode is enabled by default for development.

### Access the Web Interface

- Open `http://127.0.0.1:5000/` in your browser.
- Use the interface to:
  - Manually add expenses (amount, merchant, description).
  - Upload receipt images for automatic data extraction and classification.

### API Endpoints

- **GET /**: Renders the main web interface.
- **POST /api/classify**: Classifies an expense based on description and merchant.

  ```json
  {
    "amount": 100,
    "merchant": "kr bakery",
    "description": "dosha and egg roast"
  }
  ```

  Returns:

  ```json
  {
    "amount": 100.0,
    "merchant": "kr bakery",
    "description": "dosha and egg roast",
    "category": "food"
  }
  ```

- **POST /api/classify_image**: Processes a receipt image and classifies the expense.
  - Send a `multipart/form-data` request with an `image` field containing the receipt image.
  - Returns extracted data and category.
- **POST /api/save_expense**: Saves an expense to the CSV file.

  ```json
  {
    "amount": 100,
    "merchant": "kr bakery",
    "description": "dosha and egg roast",
    "category": "food"
  }
  ```

- **GET /api/get_expenses**: Retrieves all saved expenses. Returns:

  ```json
  [
    {
      "amount": 100.0,
      "merchant": "kr bakery",
      "description": "dosha and egg roast",
      "category": "food"
    }
  ]
  ```

- **GET /api/recommendations**: Provides spending recommendations (currently disabled due to API quota limits).

### Example: Classify an Expense

- Use a tool like `curl` or Postman to test the `/api/classify` endpoint:

  ```bash
  curl -X POST http://127.0.0.1:5000/api/classify -H "Content-Type: application/json" -d '{"amount": 100, "merchant": "teashop", "description": "chai latte"}'
  ```

  Expected output:

  ```json
  {
    "amount": 100.0,
    "merchant": "teashop",
    "description": "chai latte",
    "category": "food"
  }
  ```

## Testing

### Manual Testing

1. Start the app: `python app.py`.
2. Open `http://127.0.0.1:5000/` in your browser.
3. Add expenses manually or upload a receipt image.
4. Check the logs in the terminal for classification details.
5. Retrieve saved expenses via `GET /api/get_expenses`.

### Standalone Script Testing

The project includes a standalone script (`predict.py`) for testing the `predict_category` function independently:

```bash
python predict.py
```

This script runs predefined test cases and prints the predicted categories.

## Limitations

- **Gemini API Dependency**: The application currently relies on keyword-based classification due to Gemini API quota limits (50 requests/day on the free tier). To enable API-based classification, upgrade your Gemini API plan or wait for the quota to reset.
- **OCR Accuracy**: Tesseract OCR may struggle with low-quality images or complex receipt layouts. Preprocessing (denoising, thresholding) is applied, but accuracy depends on image quality.
- **Development Server**: The Flask development server is not suitable for production. Use a WSGI server (e.g., Gunicorn) for deployment.

## Troubleshooting

- **Tesseract Not Found**:
  - Ensure Tesseract is installed and the path in `app.py` is correct.
  - Test Tesseract from the command line: `tesseract --version`.
- **API Quota Exceeded**:
  - The app falls back to keyword-based classification if the Gemini API quota is exceeded.
  - Check your quota at the Gemini API documentation.
- **Classification Errors**:
  - Review logs for `Keyword matches` to understand why a category was chosen.
  - Update the keyword lists in `predict_category` if needed.
