#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مثال ساده برای استفاده از کلاس IranianIDCardExtractor
"""

from id_card_extractor import IranianIDCardExtractor
import os

def test_extractor():
    """
    تست کردن استخراج‌کننده کارت ملی
    """
    # ایجاد نمونه از کلاس
    extractor = IranianIDCardExtractor()
    
    # مسیر فایل تصویر (باید توسط کاربر تعیین شود)
    image_path = "sample_id_card.jpg"  # نام فایل تصویر نمونه
    
    if not os.path.exists(image_path):
        print(f"فایل تصویر {image_path} یافت نشد.")
        print("لطفاً یک فایل تصویر کارت ملی در همین پوشه قرار دهید و نام آن را 'sample_id_card.jpg' بگذارید.")
        print("یا می‌توانید مسیر فایل را در کد تغییر دهید.")
        return
    
    # پردازش کارت ملی
    result = extractor.process_id_card(image_path)
    
    if result:
        print("\n" + "="*60)
        print("نتایج استخراج اطلاعات")
        print("="*60)
        
        # نمایش اطلاعات استخراج شده
        info = result['اطلاعات_استخراج_شده']
        for field, value in info.items():
            if value and field != 'کد_ملی_معتبر':
                print(f"{field}: {value}")
        
        # نمایش وضعیت اعتبار کد ملی
        if info.get('کد_ملی'):
            validity = "معتبر" if info.get('کد_ملی_معتبر') else "نامعتبر"
            print(f"وضعیت کد ملی: {validity}")
            
        # ذخیره نتایج در فایل
        with open('extracted_info.txt', 'w', encoding='utf-8') as f:
            f.write("نتایج استخراج اطلاعات کارت ملی\n")
            f.write("="*40 + "\n\n")
            
            for field, value in info.items():
                if value and field != 'کد_ملی_معتبر':
                    f.write(f"{field}: {value}\n")
            
            if info.get('کد_ملی'):
                validity = "معتبر" if info.get('کد_ملی_معتبر') else "نامعتبر"
                f.write(f"وضعیت کد ملی: {validity}\n")
            
            f.write(f"\nمتن خام استخراج شده:\n{result['متن_خام']}")
        
        print(f"\nنتایج در فایل 'extracted_info.txt' ذخیره شد.")
        
    else:
        print("خطا در پردازش تصویر")

if __name__ == "__main__":
    test_extractor()