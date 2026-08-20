from flask import Flask, request
import easyocr
import re
import os
import cv2
import joblib
from pyzbar.pyzbar import decode
from doc_analyzer import extract_document_features

app = Flask(__name__)

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Blacklisted UPI IDs for payment fraud detection
blacklist = [
    "fraud123@upi",
    "scammer@paytm",
    "fakepay@oksbi"
]

# Load Data-Driven Machine Learning Model
doc_model_path = "doc_fraud_model.pkl"
doc_model = joblib.load(doc_model_path) if os.path.exists(doc_model_path) else None


@app.route('/')
def home():
    return '''
    <h1>FraudShield AI</h1>
    <h3>Select Verification Module:</h3>
    <ul>
        <li><a href="/verify-payment"><b>1. Payment Screenshot Verification</b> (UPI / QR / OCR Engine)</a></li>
        <li><a href="/verify-document"><b>2. Document Verification</b> (Data-Driven ML Model)</a></li>
    </ul>
    '''


# ---------------------------------------------------------
# MODULE 1: PAYMENT SCREENSHOT VERIFICATION
# ---------------------------------------------------------
@app.route('/verify-payment', methods=['GET', 'POST'])
def verify_payment():
    if request.method == 'POST':
        file = request.files['image']
        file.save('payment.jpg')

        # --- QR Code Processing ---
        qr_status = "No QR Found"
        qr_data = "None"
        upi_id = "Not Found"
        blacklist_status = "Not Blacklisted"
        amount_from_qr = "Not Found"
        url_found = []

        img = cv2.imread("payment.jpg")
        decoded_objects = decode(img)

        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")

            if qr_data.startswith("upi://"):
                qr_status = "Valid UPI QR"
                upi_match = re.search(r'pa=([^&]+)', qr_data)

                if upi_match:
                    upi_id = upi_match.group(1)
                    if upi_id in blacklist:
                        blacklist_status = "BLACKLISTED"

                amount_match = re.search(r'am=([\d.]+)', qr_data)
                if amount_match:
                    amount_from_qr = amount_match.group(1)

            elif qr_data.startswith("http"):
                qr_status = "Website QR"
                url_found.append(qr_data)
            else:
                qr_status = "QR Found (Unknown Type)"

        # --- OCR Processing ---
        result = reader.readtext("payment.jpg")
        texts = [item[1] for item in result]
        full_text = " ".join(texts)

        # URL Extraction
        ocr_urls = re.findall(r'https?://\S+|www\.\S+', full_text)
        url_found.extend(ocr_urls)

        # Amount Extraction
        amount = "Not Found"
        for t in texts:
            if re.fullmatch(r'8\d{2,}', t):
                amount = t[1:]
                break

            if re.fullmatch(r'7\d{1,3},\d{3}(?:\.\d+)?', t):
                amount = t[1:]
                break

            match = re.search(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', t)
            if match:
                amount = match.group()
                if amount.startswith("7"):
                    amount = amount[1:]
                break

            if re.fullmatch(r'\d{2,6}(?:\.\d+)?', t):
                if t not in ["2023", "2024", "2025", "2026", "6976", "0217"]:
                    amount = t

        if amount == "Not Found" and amount_from_qr != "Not Found":
            amount = amount_from_qr

        # Transaction ID Extraction
        txn_id = "Not Found"
        for t in texts:
            if re.fullmatch(r'\d{8,}', t) or re.fullmatch(r'[A-Z]\d{10,}', t):
                txn_id = t
                break

        if txn_id == "Not Found":
            for i, t in enumerate(texts):
                if "UPI transaction ID" in t and i + 1 < len(texts):
                    txn_id = texts[i + 1]
                    break
                if "Transaction ID" in t and i + 1 < len(texts):
                    txn_id = texts[i + 1]
                    break
                if "UPI Ref" in t and i + 1 < len(texts):
                    txn_id = texts[i + 1]
                    break
                if "UTR" in t:
                    txn_id = t
                    break

        # Risk Score Calculation
        score = 100
        if amount != "Not Found": score -= 25
        if txn_id != "Not Found": score -= 35
        if qr_status == "Valid UPI QR": score -= 40
        if upi_id != "Not Found": score -= 20
        if amount != "Not Found" and txn_id == "Not Found": score -= 15

        if any(w in full_text for w in ["Successful", "Successtul", "Success", "Completed", "Paid to", "Paid"]):
            score -= 30

        if len(url_found) > 0: score += 20
        if blacklist_status == "BLACKLISTED": score += 40

        score = max(0, min(score, 100))

        if score <= 20:
            status = "Likely Genuine"
        elif score <= 50:
            status = "Needs Verification"
        else:
            status = "Suspicious"

        return f"""
        <h1>FraudShield AI - Payment Report</h1>
        <p><b>Amount:</b> {amount}</p>
        <p><b>Transaction / UPI ID:</b> {txn_id}</p>
        <p><b>QR Status:</b> {qr_status}</p>
        <p><b>QR Data:</b> {qr_data}</p>
        <p><b>UPI ID:</b> {upi_id}</p>
        <p><b>Blacklist Check:</b> {blacklist_status}</p>
        <p><b>URLs Found:</b> {url_found if url_found else "None"}</p>
        <p><b>Risk Score:</b> {score}/100</p>
        <p><b>Status:</b> {status}</p>
        <br>
        <a href="/verify-payment">Analyze Another Payment</a> | <a href="/">Back to Home</a>
        """

    return '''
    <h1>FraudShield AI</h1>
    <h2>Module 1: Payment Screenshot Verification</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="image" required>
        <br><br>
        <input type="submit" value="Analyze Screenshot">
    </form>
    <br>
    <a href="/">Back to Home</a>
    '''


# ---------------------------------------------------------
# MODULE 2: DATA-DRIVEN DOCUMENT VERIFICATION
# ---------------------------------------------------------
@app.route('/verify-document', methods=['GET', 'POST'])
def verify_document():
    if request.method == 'POST':
        file = request.files['image']
        filepath = 'doc.jpg'
        file.save(filepath)

        if not doc_model:
            return "ML Model missing! Run 'python train_doc_model.py' first to generate doc_fraud_model.pkl."

        features, detected_id, full_text = extract_document_features(filepath)

        prediction = doc_model.predict([features])[0]
        probabilities = doc_model.predict_proba([features])[0]

        fraud_prob = round(float(probabilities[1]) * 100, 2)
        genuine_prob = round(float(probabilities[0]) * 100, 2)

        status = "Tampered / Fake Document" if prediction == 1 else "Authentic / Genuine Document"

        return f"""
        <h1>FraudShield AI - Document Report (ML Data-Driven)</h1>
        <p><b>Detected ID Details:</b> {detected_id}</p>
        <p><b>Model Verdict:</b> {status}</p>
        <p><b>Fraud Probability:</b> {fraud_prob}%</p>
        <p><b>Authenticity Score:</b> {genuine_prob}%</p>
        <br>
        <a href="/verify-document">Analyze Another Document</a> | <a href="/">Back to Home</a>
        """

    return '''
    <h1>FraudShield AI</h1>
    <h2>Module 2: Data-Driven Document Verification</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="image" required>
        <br><br>
        <input type="submit" value="Analyze Document">
    </form>
    <br>
    <a href="/">Back to Home</a>
    '''


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )