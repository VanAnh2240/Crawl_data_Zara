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


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__": 
    driver = init_driver()

    # =====================================================#
    # ========== Crawl detail từng sản phẩm  ============#
    # =====================================================#

    with open("product_base.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    detail_output = []

    for idx, p in enumerate(products):
        print(f"Crawling detail {idx+1}/{len(products)} - {p['product_id']}")

        try:
            detail = crawl_product_detail(driver, p["url"], p["product_id"])
            detail_output.append(detail)
        except Exception as e:
            print("Error crawling detail:", p["product_id"], e)

        # Append mỗi 10 sản phẩm
        if (idx + 1) % 10 == 0:
            append_json("product_detail.json", detail_output)
            detail_output = [] 
    
    # Ghi phần còn lại
    if detail_output:
        append_json("product_detail.json", detail_output)

    driver.quit()
    print(f"{len(products)} products detail crawled.")
