import os
import re
import json
import requests
import pandas as pd

SHEET_ID = "1nQufZBj1hNIatqtnnzyj5IofgvRUaLuhrOAeZL40pv8"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

IMAGE_FOLDER = "static/products"
JSON_OUTPUT_PATH = "static/products.json"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

def extract_drive_id(url):
    if not url or not isinstance(url, str):
        return None
    patterns = [
        r"file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"open\?id=([a-zA-Z0-9_-]+)",
        r"uc\?export=download&id=([a-zA-Z0-9_-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

print("🚀 Đang tiến hành đọc dữ liệu đơn ngôn ngữ từ Google Sheets...")

try:
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip().str.lower()

    products_list = []

    for index, row in df.iterrows():
        if pd.isna(row.get('id')):
            continue
            
        p_id = int(row['id'])
        category_lower = str(row.get('category', '')).strip().lower()
        
        # THAY ĐỔI: GOM TẤT CẢ CÁC THỂ LOẠI NƯỚC UỐNG VÀO "do-uong"
        category_mapping = {
            "cà phê": "do-uong", "ca phe": "do-uong", "ca-phe": "do-uong",
            "đồ uống": "do-uong", "do uong": "do-uong", "do-uong": "do-uong",
            "trà trái cây": "do-uong", "tra trai cay": "do-uong",
            "trà sữa": "do-uong", "tra sua": "do-uong",
            "nước ngọt": "do-uong", "nuoc ngot": "do-uong",
            "ăn vặt": "an-vat", "an vat": "an-vat", "món ăn vặt": "an-vat"
        }
        final_category = category_mapping.get(category_lower, "do-uong") # Mặc định nếu điền lệch sẽ đẩy vào đồ uống

        drive_url = str(row.get('image', '')).strip()
        drive_id = extract_drive_id(drive_url)
        image_json_path = "https://placehold.co/400x300?text=Cafe+Moc"

        if drive_id:
            image_filename = f"product_{p_id}.jpg"
            local_image_path = os.path.join(IMAGE_FOLDER, image_filename)
            try:
                download_file_from_google_drive(drive_id, local_image_path)
                image_json_path = f"static/products/{image_filename}"
            except Exception as img_err:
                print(f"❌ Lỗi tải ảnh món {p_id}: {img_err}")
                if os.path.exists(local_image_path):
                    image_json_path = f"static/products/{image_filename}"
        elif drive_url and drive_url != 'nan':
            image_json_path = drive_url

        product_item = {
            "id": p_id,
            "category": final_category,
            "name_vi": str(row.get('name_vi', '')).strip(),
            "description_vi": str(row.get('description_vi', '')).strip(),
            "price_vi": str(row.get('price_vi', '')).strip(),
            "image": image_json_path
        }
        products_list.append(product_item)

    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as json_file:
        json.dump(products_list, json_file, ensure_ascii=False, indent=4)
        
    print(f"🎉 Hoàn thành! Đã lưu file thực đơn 2 phân loại tại {JSON_OUTPUT_PATH}")

except Exception as e:
    print(f"❌ Lỗi đồng bộ: {e}")