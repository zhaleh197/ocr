#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import pytesseract
import re
import numpy as np
from PIL import Image, ImageEnhance
import os
import sys

class IranianIDCardExtractor:
    def __init__(self):
        """
        کلاس استخراج اطلاعات کارت ملی ایرانی
        """
        # تنظیمات Tesseract برای زبان فارسی
        self.tesseract_config = r'--oem 3 --psm 6 -l fas+eng'
        
    def preprocess_image(self, image_path):
        """
        پیش‌پردازش تصویر برای بهبود تشخیص متن
        """
        try:
            # خواندن تصویر
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"نمی‌توان تصویر را از مسیر {image_path} بارگذاری کرد")
            
            # تبدیل به خاکستری
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # اعمال فیلتر گاوسی برای کاهش نویز
            denoised = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # تنظیم کنتراست و روشنایی
            alpha = 1.5  # کنتراست
            beta = 30    # روشنایی
            enhanced = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
            
            # اعمال threshold برای بهبود کیفیت متن
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # حذف نویز با عملیات مورفولوژی
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            return cleaned
            
        except Exception as e:
            print(f"خطا در پیش‌پردازش تصویر: {str(e)}")
            return None
    
    def extract_text_from_image(self, processed_image):
        """
        استخراج متن از تصویر پردازش شده
        """
        try:
            # تبدیل تصویر OpenCV به PIL
            pil_image = Image.fromarray(processed_image)
            
            # بهبود کیفیت تصویر
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(2.0)
            
            # استخراج متن با Tesseract
            extracted_text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)
            
            return extracted_text
            
        except Exception as e:
            print(f"خطا در استخراج متن: {str(e)}")
            return ""
    
    def parse_id_card_info(self, text):
        """
        تجزیه و تحلیل متن استخراج شده و شناسایی اطلاعات کارت ملی
        """
        info = {
            'نام': None,
            'نام_خانوادگی': None,
            'نام_پدر': None,
            'کد_ملی': None,
            'تاریخ_تولد': None,
            'محل_تولد': None,
            'شماره_شناسنامه': None
        }
        
        # الگوهای regex برای شناسایی اطلاعات
        patterns = {
            'کد_ملی': r'(\d{10})',
            'تاریخ_تولد': r'(\d{4}/\d{1,2}/\d{1,2})',
            'شماره_شناسنامه': r'شناسنامه.*?(\d+)',
            'نام': r'نام\s*:?\s*([^\n\r]+)',
            'نام_خانوادگی': r'نام خانوادگی\s*:?\s*([^\n\r]+)',
            'نام_پدر': r'نام پدر\s*:?\s*([^\n\r]+)',
            'محل_تولد': r'محل تولد\s*:?\s*([^\n\r]+)'
        }
        
        # جستجو برای هر الگو
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.MULTILINE | re.UNICODE)
            if matches:
                # انتخاب اولین مطابقت معتبر
                for match in matches:
                    if field == 'کد_ملی' and len(match) == 10:
                        info[field] = match
                        break
                    elif field == 'تاریخ_تولد':
                        info[field] = match
                        break
                    elif field in ['نام', 'نام_خانوادگی', 'نام_پدر', 'محل_تولد']:
                        cleaned_match = match.strip()
                        if len(cleaned_match) > 1:
                            info[field] = cleaned_match
                            break
                    elif field == 'شماره_شناسنامه':
                        info[field] = match
                        break
        
        return info
    
    def validate_national_id(self, national_id):
        """
        اعتبارسنجی کد ملی ایرانی
        """
        if not national_id or len(national_id) != 10:
            return False
        
        # بررسی اینکه همه ارقام یکسان نباشند
        if len(set(national_id)) == 1:
            return False
        
        # محاسبه رقم کنترل
        check_sum = 0
        for i in range(9):
            check_sum += int(national_id[i]) * (10 - i)
        
        remainder = check_sum % 11
        
        if remainder < 2:
            return int(national_id[9]) == remainder
        else:
            return int(national_id[9]) == 11 - remainder
    
    def process_id_card(self, image_path):
        """
        پردازش کامل کارت ملی و استخراج اطلاعات
        """
        print(f"در حال پردازش تصویر: {image_path}")
        
        # پیش‌پردازش تصویر
        processed_image = self.preprocess_image(image_path)
        if processed_image is None:
            return None
        
        # استخراج متن
        extracted_text = self.extract_text_from_image(processed_image)
        if not extracted_text:
            print("متنی در تصویر شناسایی نشد")
            return None
        
        print("متن استخراج شده:")
        print("-" * 50)
        print(extracted_text)
        print("-" * 50)
        
        # تجزیه اطلاعات
        parsed_info = self.parse_id_card_info(extracted_text)
        
        # اعتبارسنجی کد ملی
        if parsed_info['کد_ملی']:
            is_valid = self.validate_national_id(parsed_info['کد_ملی'])
            parsed_info['کد_ملی_معتبر'] = is_valid
        
        return {
            'متن_خام': extracted_text,
            'اطلاعات_استخراج_شده': parsed_info
        }

def main():
    """
    تابع اصلی برنامه
    """
    if len(sys.argv) != 2:
        print("استفاده: python id_card_extractor.py <مسیر_تصویر>")
        print("مثال: python id_card_extractor.py id_card.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"فایل تصویر در مسیر {image_path} یافت نشد")
        sys.exit(1)
    
    # ایجاد نمونه از کلاس استخراج‌کننده
    extractor = IranianIDCardExtractor()
    
    # پردازش کارت ملی
    result = extractor.process_id_card(image_path)
    
    if result:
        print("\n" + "="*60)
        print("نتایج استخراج اطلاعات کارت ملی")
        print("="*60)
        
        info = result['اطلاعات_استخراج_شده']
        for field, value in info.items():
            if value:
                print(f"{field}: {value}")
        
        if info.get('کد_ملی'):
            validity = "معتبر" if info.get('کد_ملی_معتبر') else "نامعتبر"
            print(f"وضعیت کد ملی: {validity}")
    else:
        print("خطا در پردازش تصویر")

if __name__ == "__main__":
    main()