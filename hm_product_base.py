from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import os
from urllib.parse import urlparse, parse_qs

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
# HÀM LẤY SUB CATEGORY
# =====================================================
def get_subcategories(driver, parent_url):
    driver.get(parent_url)
    time.sleep(3)

    subcats = []

    try:
        items = driver.find_elements(By.CSS_SELECTOR, "nav[aria-label='categories'] ul li a")
        for item in items:
            href = item.get_attribute("href")
            name = item.text.strip()
            if href:
                subcats.append({
                    'href': href,
                    'name': name
                })
    except:
        pass

    return subcats


# =====================================================
# HÀM CRAWL SẢN PHẨM TRONG CATEGORY
# =====================================================
def crawl_category_products(driver, url):
    page = 1
    product_list = []
    seen_ids = set()
    
    # categoryID
    categoryID = url['name']
    base_url = url['href']

    while True:
        page_url = f"{base_url}?page={page}"
        print(f"   Crawling page {page_url}")

        driver.get(page_url)
        time.sleep(3)

        try:
            products = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "ul[data-elid='product-grid'] > li")
                )
            )
        except:
            print("     +Product listing not found")
            break

        if not products:
                print("   No products found, end of category.")
                break
        print(f"     +{len(products)} products found on page")

        for i in range(len(products)):
            # mỗi lần truy cập lại product[i] để tránh stale
            products = driver.find_elements(By.CSS_SELECTOR, "ul[data-elid='product-grid'] > li")
            product = products[i]   

            #==== PRODUCT ID =====
            try:
                productID = product.find_element(By.CSS_SELECTOR, "article").get_attribute("data-articlecode")
            except Exception as e:
                print("Error productID:", e)
                productID = None
            
            # ==== NAME =====
            try:
                name = product.find_element(By.CSS_SELECTOR, "div.e221e1 h2").text.strip()
            except Exception as e:
                print("Error name:", e)
                name = None

            # ===== PRICE =====
            try:
                del_el = product.find_elements(By.CSS_SELECTOR, "p.dbe41e del")
                if del_el:
                    price = del_el[0].text.strip()
                else:
                    span_el = product.find_element(By.CSS_SELECTOR, "p.dbe41e span")
                    price = span_el.text.strip()
            except Exception as e:
                print("Error price:", e) 
                price = None

            # ===== IMAGE =====
            try:
                img_el = product.find_element(By.CSS_SELECTOR, "img")
                alt = img_el.get_attribute("alt")
                srcset = img_el.get_attribute("srcset")
                
                if srcset:
                    srcset_items = [item.strip() for item in srcset.split(",") if item.strip()]
                    if srcset_items:
                        image_link = srcset_items[-1].split()[0]
                    else:
                        image_link = img_el.get_attribute("src")
                else:
                    image_link = img_el.get_attribute("src")
            except Exception as e:
                print("Error image:", e)
                image_link = None
                alt = None

            # ===== PRODUCT URL =====
            try:
                product_url = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            except Exception as e:
                print("Error product URL:", e)
                product_url = None
            
            # ===== ADD TO LIST =====
            product_list.append({
                "product_id": productID,
                "categoriesID": categoryID,
                "name": name,
                "price": price,
                "image": {"image_link": image_link, "alt": alt},
                "url": product_url
            })

        page += 1
        time.sleep(1)

    return product_list, categoryID


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__": 
    driver = init_driver()

    # =====================================================#
    # ========== 1. CRAWL CATEGORY (product base) =========#
    # =====================================================#
    
    urls = [
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/dam.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao-khoac-cardigan-va-ao-len.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/quandai.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao-khoac-ao-khoac-dai.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao-hoodie-ao-ni.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/quan-jean.html",
        #"https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao-blazer-va-ao-gi-le.html",
        "https://www2.hm.com/vi_vn/nu/goi-y-san-pham/ao-so-mi-va-ao-kieu.html",
        "https://www2.hm.com/vi_vn/nu/goi-y-san-pham/chan-vay.html",
        "https://www2.hm.com/vi_vn/nu/goi-y-san-pham/do-ngu.html",
        "https://www2.hm.com/vi_vn/nu/goi-y-san-pham/quan-short.html",
    ]

    total_products = 0

    for category_url in urls:
        print("CATEGORY ROOT:", category_url)
        
        # ===== LẤY SUB-CATEGORY =====
        subcats = get_subcategories(driver, category_url)
        print(f" Found {len(subcats)} sub-categories")

        # Nếu không có sub-category → crawl trực tiếp category gốc
        if not subcats:
            subcats = [category_url]
            start_index = 0
        else:
            start_index = 1

        # ===== CRAWL TỪNG SUB-CATEGORY =====
        for sub_url in subcats[start_index:]:
            products, cateID = crawl_category_products(driver, sub_url)

            append_json("hm_product_base.json", products)
            
            total_products += len(products)

            print(f"   Crawled {len(products)} products")

    driver.quit()
    print(f" DONE! {total_products} total products crawled")
    