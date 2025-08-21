#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import cv2
import pytesseract
import re
import numpy as np
from PIL import Image, ImageEnhance
import io
import tempfile
import os
from typing import Optional, Dict, Any

app = FastAPI(title="ID Card OCR API", description="API for extracting information from Iranian ID cards", version="1.0.0")

class IranianIDCardExtractor:
    def __init__(self):
        """
        Iranian ID Card information extractor class
        """
        # Tesseract configuration for Persian and English
        self.tesseract_config = r'--oem 3 --psm 6 -l fas+eng'
        
    def preprocess_image(self, image_array):
        """
        Preprocess image for better text recognition
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian filter to reduce noise
            denoised = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Adjust contrast and brightness
            alpha = 1.5  # Contrast
            beta = 30    # Brightness
            enhanced = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
            
            # Apply threshold for better text quality
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Remove noise with morphological operations
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            return cleaned
            
        except Exception as e:
            raise Exception(f"Error in image preprocessing: {str(e)}")
    
    def extract_text_from_image(self, processed_image):
        """
        Extract text from processed image
        """
        try:
            # Convert OpenCV image to PIL
            pil_image = Image.fromarray(processed_image)
            
            # Enhance image quality
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(2.0)
            
            # Extract text with Tesseract
            extracted_text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
            
            return extracted_text
            
        except Exception as e:
            raise Exception(f"Error in text extraction: {str(e)}")
    
    def parse_id_card_info(self, text):
        """
        Parse extracted text and identify ID card information
        """
        info = {
            'first_name': None,
            'last_name': None,
            'father_name': None,
            'national_id': None,
            'birth_date': None,
            'birth_place': None,
            'certificate_number': None
        }
        
        # Regex patterns for identifying information
        patterns = {
            'national_id': r'(\d{10})',
            'birth_date': r'(\d{4}/\d{1,2}/\d{1,2})',
            'certificate_number': r'شناسنامه.*?(\d+)',
            'first_name': r'نام\s*:?\s*([^\n\r]+)',
            'last_name': r'نام خانوادگی\s*:?\s*([^\n\r]+)',
            'father_name': r'نام پدر\s*:?\s*([^\n\r]+)',
            'birth_place': r'محل تولد\s*:?\s*([^\n\r]+)'
        }
        
        # Search for each pattern
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.MULTILINE | re.UNICODE)
            if matches:
                # Select first valid match
                for match in matches:
                    if field == 'national_id' and len(match) == 10:
                        info[field] = match
                        break
                    elif field == 'birth_date':
                        info[field] = match
                        break
                    elif field in ['first_name', 'last_name', 'father_name', 'birth_place']:
                        cleaned_match = match.strip()
                        if len(cleaned_match) > 1:
                            info[field] = cleaned_match
                            break
                    elif field == 'certificate_number':
                        info[field] = match
                        break
        
        return info
    
    def validate_national_id(self, national_id):
        """
        Validate Iranian national ID
        """
        if not national_id or len(national_id) != 10:
            return False
        
        # Check that all digits are not the same
        if len(set(national_id)) == 1:
            return False
        
        # Calculate check digit
        check_sum = 0
        for i in range(9):
            check_sum += int(national_id[i]) * (10 - i)
        
        remainder = check_sum % 11
        
        if remainder < 2:
            return int(national_id[9]) == remainder
        else:
            return int(national_id[9]) == 11 - remainder
    
    def process_id_card_from_bytes(self, image_bytes):
        """
        Process ID card from image bytes and extract information
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Could not decode image from uploaded file")
            
            # Preprocess image
            processed_image = self.preprocess_image(img)
            
            # Extract text
            extracted_text = self.extract_text_from_image(processed_image)
            if not extracted_text:
                raise ValueError("No text detected in image")
            
            # Parse information
            parsed_info = self.parse_id_card_info(extracted_text)
            
            # Validate national ID
            if parsed_info['national_id']:
                is_valid = self.validate_national_id(parsed_info['national_id'])
                parsed_info['national_id_valid'] = is_valid
            else:
                parsed_info['national_id_valid'] = False
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'extracted_info': parsed_info
            }
            
        except Exception as e:
            raise Exception(f"Error processing ID card: {str(e)}")

# Create global extractor instance
extractor = IranianIDCardExtractor()

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "ID Card OCR API",
        "version": "1.0.0",
        "endpoints": {
            "ocrfromidcard": "POST /ocrfromidcard - Upload an ID card image to extract information"
        }
    }

@app.post("/ocrfromidcard")
async def ocr_from_id_card(file: UploadFile = File(...)):
    """
    Extract information from an uploaded ID card image
    
    Parameters:
    - file: Image file (JPEG, PNG, etc.)
    
    Returns:
    - JSON object with extracted information
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read file contents
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Process the image
        result = extractor.process_id_card_from_bytes(contents)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "ID Card OCR API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)