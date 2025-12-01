import json
import json
import time
import random
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =====================================================
# HÀM GHI APPEND FILE JSON
# =====================================================
def append_json(filename, new_data):
    # Nếu dữ liệu là 1 object -> chuyển thành list để dễ append
    if not isinstance(new_data, list):
        new_data = [new_data]

    # Nếu file tồn tại -> load lên rồi append
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except:
                existing = []

        if not isinstance(existing, list):
            existing = []

        existing.extend(new_data)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    else:
        # File chưa có -> tạo mới
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)


# =====================================================
# KHỞI TẠO DRIVER
# =====================================================
def init_driver():
    options = Options()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# =====================================================
# APPEND JSON
# =====================================================
def append_json(filename, new_data):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []
        existing_data.extend(new_data)
        data_to_write = existing_data
    else:
        data_to_write = new_data

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data_to_write, f, ensure_ascii=False, indent=2)


# =====================================================
# HÀM CRAWL CHI TIẾT PRODUCT
# =====================================================
def crawl_product_detail(driver, url, product_id):
    driver.get(url)

    #Load trang ổn định
    wait = WebDriverWait(driver, 10)
    
    # Lấy các thành phần chính
    try:
        info_item = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-detail-view-std"))
        )
        main_el = info_item.find_element(By.CSS_SELECTOR, "div.product-detail-view__main-content")
        snd_el = info_item.find_element(By.CSS_SELECTOR, "div.product-detail-view__secondary-content")
        extra_el = info_item.find_element(By.CSS_SELECTOR, "ul.product-detail-view__extra-images")
        
    except Exception as e:
        print("Error info_item:", e)
        return None

    # Description
    try:
        desc_el = main_el.find_element(By.CSS_SELECTOR, "div.product-detail-info__description")
        description = desc_el.text.strip()
    except Exception as e:
        print("Error description:", e)
        description = None

    # Colors
    try:
        color_item = main_el.find_element(By.CSS_SELECTOR, ".product-color-extended-name")
        color = color_item.text.strip()
        color = color.split("|")[0].strip()
    except Exception as e:
        print("Error color:", e)
        color = None

    # Composition
    try:
        comp_el = info_item.find_element(By.CSS_SELECTOR, "div.product-detail-composition")
        composition = comp_el.text.strip()
        composition = " | ".join([line.strip() for line in composition.splitlines() if line.strip()])
    
    except Exception as e:
        print("Error composition:", e)
        composition = None

    # Images
    images = []
    try:
        # Images main
        img_main_el = main_el.find_element(By.CSS_SELECTOR, "div.product-detail-view__main-image-wrapper")
        try:
            img_main_tag = img_main_el.find_element(By.CSS_SELECTOR, "img.media-image__image")
            img_main_link =  img_main_tag.get_attribute("src")
            img_main_alt = img_main_tag.get_attribute("alt")        
            images.append({
                        "image_link": img_main_link,
                        "image_alt": img_main_alt
                    })
        except Exception as e:
            print("Error main image:", e)
        
        # Images secondary
        img_snd_el = snd_el.find_element(By.CSS_SELECTOR, "button.product-detail-view__secondary-image")
        try:
            source_snd_tag = img_snd_el.find_element(By.CSS_SELECTOR, "source")          
            img_snd_link =  source_snd_tag.get_attribute("srcset")
            img_snd_tag = img_snd_el.find_element(By.CSS_SELECTOR, "img.media-image__image")
            img_snd_alt = img_snd_tag.get_attribute("alt")        
            
            images.append({
                        "image_link": img_snd_link,
                        "image_alt": img_snd_alt
                    })
        except Exception as e:
            print("Error secondary image:", e)
    

        # Images extra
        try:
            img_extra_el = extra_el.find_elements(By.CSS_SELECTOR, "li.product-detail-view__extra-image-wrapper")
            for li in img_extra_el:
                try:
                    source_extra_tag = li.find_element(By.CSS_SELECTOR, "source")          
                    img_extra_link =  source_extra_tag.get_attribute("srcset")
                    img_extra_tag = li.find_element(By.CSS_SELECTOR, "img.media-image__image")
                    img_extra_alt = img_extra_tag.get_attribute("alt")
                    
                    images.append({
                        "image_link": img_extra_link,
                        "image_alt": img_extra_alt
                    })
                except Exception as e:
                    print("Error extra image:", e)

        except Exception as e:
            print("Error extra images list:", e)
          
    except Exception as e:
        print("Error images:", e)
    

    # RETURN DATA
    return {
        "product_id": product_id,
        "description": description,
        "colors": color,
        "composition": composition,
        "images": images
    }



import json
import time
import random


# === Lấy URL từ product_base.json ===
def get_urls_by_ids(product_ids, file_path='product_base.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Giả sử products là list of dict có 'product_id' và 'url'
    product_dict = {str(p['product_id']): p.get('url', None) for p in products}
    
    # Lọc các product_id cần
    return {pid: product_dict.get(str(pid)) for pid in product_ids}

# === Recrawl các product ===
def recrawl_products(driver, product_ids, output_file='product_base_recrawl.json'):
    id_url_dict = get_urls_by_ids(product_ids)
    
    for idx, (pid, url) in enumerate(id_url_dict.items(), start=1):
        if url is None:
            print(f"[{idx}/{len(id_url_dict)}] Product {pid} URL not found, skip")
            continue
        
        print(f"[{idx}/{len(id_url_dict)}] Crawling product {pid}")
        data = crawl_product_detail(driver, url, pid)
        
        if data:
            append_json(output_file, data)
        
        # Random sleep tránh bị block
        time.sleep(random.uniform(1.5, 3.0))


if __name__ == "__main__":
    # === Danh sách product_id cần recrawl ===
    urls = [
        "https://www.zara.com/vn/vi/-p478958109.html?v1=478958109&v2=2419032",
        
    ]

    # === Khởi tạo driver ===
    driver = init_driver()
    
    # === Recrawl và lưu vào file ===
    recrawl_products(driver, product_ids_to_recrawl, output_file='recrawl.json')
    
    driver.quit()
    print("Recrawl hoàn tất! Dữ liệu được lưu vào recrawl.json")

