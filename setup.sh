#!/bin/bash

echo "=== نصب و راه‌اندازی سیستم استخراج اطلاعات کارت ملی ==="

# بررسی وجود Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 یافت نشد. لطفاً ابتدا Python 3 را نصب کنید."
    exit 1
fi

# بررسی وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 یافت نشد. در حال نصب pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# نصب Tesseract OCR
echo "در حال نصب Tesseract OCR..."
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fas

# نصب کتابخانه‌های Python
echo "در حال نصب کتابخانه‌های Python..."
pip3 install -r requirements.txt

# تست نصب
echo "در حال تست نصب..."
python3 -c "import cv2, pytesseract, PIL; print('همه کتابخانه‌ها با موفقیت نصب شدند!')"

# اعطای مجوز اجرا به فایل Python
chmod +x id_card_extractor.py

echo "=== نصب با موفقیت تکمیل شد! ==="
echo ""
echo "برای استفاده از برنامه:"
echo "python3 id_card_extractor.py <مسیر_فایل_تصویر>"
echo ""
echo "مثال:"
echo "python3 id_card_extractor.py my_id_card.jpg"