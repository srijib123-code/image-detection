import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import easyocr
import re

reader = easyocr.Reader(['en'])

def get_ela_variance(image_path):
    """Calculates Error Level Analysis (ELA) to detect digital tampering."""
    try:
        original = Image.open(image_path).convert('RGB')
        resaved_path = 'temp_ela.jpg'
        original.save(resaved_path, 'JPEG', quality=90)
        resaved = Image.open(resaved_path)
        
        ela_img = ImageChops.difference(original, resaved)
        extrema = ela_img.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        
        ela_img = ImageEnhance.Brightness(ela_img).enhance(255.0 / max_diff)
        return float(np.var(np.array(ela_img)))
    except Exception:
        return 0.0

def extract_document_features(image_path):
    """Extracts ML feature vector + text details."""
    ela_score = get_ela_variance(image_path)
    
    img = cv2.imread(image_path)
    height, width, _ = img.shape
    aspect_ratio = width / float(height)
    
    ocr_results = reader.readtext(image_path)
    texts = [item[1] for item in ocr_results]
    full_text = " ".join(texts)
    
    text_count = len(ocr_results)
    confidences = [item[2] for item in ocr_results] if ocr_results else [0]
    avg_conf = float(np.mean(confidences))
    
    pil_img = Image.open(image_path)
    raw_info = str(pil_img.info).lower()
    has_edit_meta = 1.0 if any(t in raw_info for t in ['photoshop', 'canva', 'gimp', 'pixlr', 'adobe']) else 0.0
    
    # Feature vector matching model training: [ELA, Aspect Ratio, Text Count, Mean Conf, Meta Flag]
    feature_vector = [ela_score, aspect_ratio, text_count, avg_conf, has_edit_meta]
    
    # Simple regex for identity extraction
    pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', full_text)
    aadhaar_match = re.search(r'\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b', full_text)
    
    detected_id = "None"
    if pan_match:
        detected_id = f"PAN: {pan_match.group()}"
    elif aadhaar_match:
        detected_id = f"Aadhaar: {aadhaar_match.group()}"
        
    return feature_vector, detected_id, full_text