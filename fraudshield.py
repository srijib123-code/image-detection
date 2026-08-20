import easyocr
import cv2
import re

print("=== FraudShield AI ===")

img = cv2.imread("payment.jpg")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

cv2.imwrite("processed.jpg", gray)

reader = easyocr.Reader(['en'])

result = reader.readtext("processed.jpg")

texts = [item[1] for item in result]

full_text = " ".join(texts)

print("\nOCR TEXT:")
print(full_text)

amount = "Not Found"

for t in texts:

    t = t.replace("₹", "")
    t = t.replace("7,", ",")

    match = re.search(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', t)

    if match:
        amount = match.group()
        break

txn_id = "Not Found"

for i, t in enumerate(texts):

    if "Transaction ID" in t and i + 1 < len(texts):
        txn_id = texts[i + 1]
        break

    if "UPI transaction ID" in t and i + 1 < len(texts):
        txn_id = texts[i + 1]
        break

print("\nAmount:", amount)
print("Transaction ID:", txn_id)