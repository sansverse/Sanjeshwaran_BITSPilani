
---

# **HealthRx Bill Extraction API**

Accurate Line-Item Extraction from Medical Bills using OCR + Groq LLM

---

## **📌 Overview**

This project is built for the **HackRx Datathon IIT** challenge.
The task is to **extract structured line-item billing data** from multi-page medical invoices and compute totals **without double counting**.

The system uses:

* **PaddleOCR (PP-OCRv4)** → Extract raw text from bill images/PDFs
* **Groq LLM (llama-3.1-8b-instant)** → Convert OCR text into structured JSON
* **FastAPI** → Production-ready API endpoint
* **ngrok / Cloud deployment** → To expose the endpoint publicly

The output strictly follows the required **submission schema**.

---

## **📂 Repository Structure**

```
app/
 ├── main.py                # FastAPI entry point
 ├── ocr_engine.py          # OCR extraction (PaddleOCR)
 ├── extract.py             # LLM structured extraction logic (Groq API)
 ├── __init__.py
.env                        # Contains GROQ_API_KEY
requirements.txt
README.md
```

---

## **🔧 Installation & Setup**

### **1️⃣ Clone the repository**

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### **2️⃣ Create a virtual environment**

```bash
python -m venv .venv
```

### **3️⃣ Activate environment**

#### Windows (PowerShell):

```powershell
.\.venv\Scripts\activate
```

### **4️⃣ Install dependencies**

```bash
pip install -r requirements.txt
```

### **5️⃣ Add your Groq API key**

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

---

## **🚀 Running the API locally**

Start the server:

```bash
uvicorn app.main:app --reload
```

API Documentation will be available at:

```
http://127.0.0.1:8000/docs
```

Health check:

```
GET /health
```

---

## **🌐 Exposing with ngrok (optional)**

In a *new terminal* (while API is running):

```bash
ngrok http 8000
```

You will get a public URL such as:

```
https://xyz.ngrok-free.dev
```

Your deployed API will now be available at:

```
POST https://xyz.ngrok-free.dev/extract-bill-data
```

---

## **🧠 How the System Works**

### **Step 1 — File Download**

The API downloads the bill using the `document` URL.

### **Step 2 — OCR Extraction**

`ocr_engine.py` extracts text from images (PNG/JPG) using PaddleOCR.

### **Step 3 — LLM Interpretation**

`extract.py` sends OCR text to Groq LLM with instructions:

* Identify page type
* Extract line items, quantities, rates, net amounts
* Avoid duplicates
* Return valid JSON following strict schema

### **Step 4 — FastAPI Response**

The API returns a **fully structured JSON** as required.

---

## **📤 API Usage**

### **Request**

```
POST /extract-bill-data
Content-Type: application/json
```

### **Body**

```json
{
  "document": "https://your-document-url"
}
```

### **Response Format**

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1000,
    "input_tokens": 600,
    "output_tokens": 400
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Injection XYZ",
            "item_amount": 230.50,
            "item_rate": 115.25,
            "item_quantity": 2
          }
        ]
      }
    ],
    "total_item_count": 14
  }
}
```

---

## **📈 Evaluation Notes (Problem Statement Requirements)**

Your API is designed to match the competition rubric:

✔ Extract *all* line items
✔ Prevent double counting
✔ Compute consistent totals
✔ Distinguish between page types
✔ Follow the required JSON schema *exactly*
✔ Designed for automated evaluation systems

---

## **🛠 Technologies Used**

| Component   | Technology                          |
| ----------- | ----------------------------------- |
| OCR         | PaddleOCR (PP-OCRv4)                |
| LLM         | meta-llama/llama-4-scout-17b-16e-instruct      |
| Backend     | FastAPI                             |
| Environment | Python 3.10                         |
| Deployment  | ngrok (for testing) & cloud options |

---

## **☁ Recommended Deployment Options**

You can deploy easily using:

* **Render.com (Free Tier)**
* **Railway.app**
* **Fly.io**
* **Azure App Service**
* **GitHub Codespaces** (if allowed)

Deployment instructions can be added on request.

---

## **✍ Author**

**Sanjeshwaran L**
Email: *sanjeshwaran26@gmail.com*
GitHub: *@sansverse*

---


