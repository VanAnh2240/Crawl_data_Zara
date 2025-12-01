import json
import os
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    wait = WebDriverWait(driver, 20)

    time.sleep(random.uniform(2, 4))  

    # ===== DESCRIPTION =====
    description = None
    try:     
        toggle_btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button#toggle-descriptionAccordion"))
        )
        
        if toggle_btn.get_attribute("aria-expanded") == "false":
            driver.execute_script("arguments[0].click();", toggle_btn)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "section-descriptionAccordion"))
            )
        
        desc_container = driver.find_element(By.ID, "section-descriptionAccordion")
        description = desc_container.text.strip()
    except Exception as e:
        print("Description not found:", e)
    
    # ===== COMPOSITION =====
    composition = None
    try:  
        toggle_btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#toggle-materialsAndSuppliersAccordion"))
        )
        
        if toggle_btn.get_attribute("aria-expanded") == "false":
            driver.execute_script("arguments[0].click();", toggle_btn)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "section-materialsAndSuppliersAccordion"))
            )
        
        desc_container = driver.find_element(By.ID, "section-materialsAndSuppliersAccordion")
        composition_el = desc_container.find_element(By.CSS_SELECTOR, "div.a34b1b > ul.e7b1d5")
        composition = composition_el.text.strip()
    except Exception as e:
        print("Composition not found:", e)

    # ===== COLORS & MAIN IMAGES =====
    color_data = []
    try:
        color_thumbnails = wait.until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, "div[data-testid='grid'] a[role='radio']"
            ))
        )

        for thumb in color_thumbnails:
            color_name = thumb.get_attribute("title").strip()
            driver.execute_script("arguments[0].click();", thumb)

            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[data-testid='grid-gallery'] img"))
            )
            try:
                gallery = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul[data-testid='grid-gallery']"))
                )
                img_elements = gallery.find_elements(By.CSS_SELECTOR, "img")

                image_links = []
                for img in img_elements:
                    srcset = img.get_attribute("srcset")
                    if srcset:
                        image_link = srcset.split(",")[-1].strip().split()[0]
                        image_links.append(image_link)

                color_data.append({
                    'color_name': color_name,
                    'image_links': image_links
                })
            except Exception as e:
                print("Error color_thumbnails ", e)
    except Exception as e:
        print("Colors/images not found:", e)

    # ===== RETURN DATA =====
    return {
        "product_id": product_id,
        "description": description,
        "composition": composition,
        "colors": color_data
    }

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__": 
    driver = init_driver()

    # =====================================================#
    # ========== Crawl detail từng sản phẩm  ============#
    # =====================================================#

    with open("hm_product_base.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    detail_output = []

    for idx, p in enumerate(products):
        print(f"Crawling detail {idx+1}/{len(products)} - {p['product_id']}")

        try:
            detail = crawl_product_detail(driver, p["url"], p["product_id"])
            detail_output.append(detail)
        except Exception as e:
            print("Error crawling detail:", p["product_id"], e)

        time.sleep(random.uniform(3, 6))

        # Append mỗi 10 sản phẩm
        if (idx + 1) % 1 == 0:
            append_json("hm_product_detail.json", detail_output)
            detail_output = [] 
    
    # Ghi phần còn lại
    if detail_output:
        append_json("hm_product_detail.json", detail_output)

    driver.quit()
    print(f"{len(products)} products detail crawled.")
