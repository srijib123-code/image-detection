import easyocr
import cv2

print("Starting OCR Test...")

img = cv2.imread("payment.jpg")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

cv2.imwrite("processed.jpg", gray)

reader = easyocr.Reader(['en'])

result = reader.readtext("processed.jpg")

print("\n===== DETECTED TEXT ONLY =====\n")

for item in result:
    print(item[1])

print("\n===== FULL OCR DATA =====\n")

for item in result:
    print(item)