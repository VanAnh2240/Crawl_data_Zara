from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
from urllib.parse import urlparse, parse_qs

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
# HÀM LOAD TOÀN BỘ SẢN PHẨM TRONG CATEGORY
# =====================================================
def load_all_products(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    
    while True:
        try:
            # Scroll xuống đáy
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Chờ nút load more xuất hiện
            btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a div.fr-load-more"))
            )

            driver.execute_script("arguments[0].click();", btn)
            print("Clicked load more button")

            # Chờ sản phẩm mới load xong (ví dụ chờ số lượng article tăng)
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "article[data-test^='product-card']")) > 0)
        except Exception:
            print("No load more button — All products loaded")
            break

# =====================================================
# HÀM CRAWL SẢN PHẨM TRONG CATEGORY
# =====================================================
def crawl_category_products(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    
    # Load toàn bộ sản phẩm
    load_all_products(driver)

    parsed_url = urlparse(url)
    categoriesID = parsed_url.path.strip("/").split("/")[-1]

    product_list = []
    all_images = []

    while True:
        # Lấy tất cả sản phẩm hiện tại
        product_items = driver.find_elements(By.CSS_SELECTOR, "article[data-test^='product-card']")
        if not product_items:
            break

        for product in product_items:
            # ===== PRODUCT ID =====
            try:
                productID = product.find_element(By.CSS_SELECTOR, "a").get_attribute("data-label")
            except:
                productID = None

            try:
                name = product.find_element(By.CSS_SELECTOR, "h3.product-tile-product-description").text.strip()
            except:
                name = None

            # ===== PRICE =====
            price = None
            try:
                price_elements = product.find_elements(By.CSS_SELECTOR, "span.price-original-ER span.fr-price-currency span")
                if price_elements:
                    price = price_elements[0].text.strip()
                else:
                    dual_price_elements = product.find_elements(By.CSS_SELECTOR, "div.dual-price-original-ER span.fr-price-currency span")
                    if dual_price_elements:
                        price = dual_price_elements[0].text.strip()
            except:
                price = None

            # ===== IMAGE =====
            try:
                img_el = product.find_element(By.CSS_SELECTOR, "img.thumb-img")
                image_link = img_el.get_attribute("src")
                alt = img_el.get_attribute("alt")
            except:
                image_link = None
                alt = None

            if image_link:
                all_images.append({
                    "product_id": productID,
                    "image_url": image_link,
                    "alt": alt
                })

            # ===== PRODUCT URL =====
            try:
                product_url = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            except:
                product_url = None

            # ===== ADD TO LIST =====
            product_list.append({
                "product_id": productID,
                "categoriesID": categoriesID,
                "name": name,
                "price": price,
                "image": {"image_link": image_link, "alt": alt},
                "url": product_url
            })
        break

    return product_list, all_images, categoriesID


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__": 
    driver = init_driver()


    # =====================================================#
    # ========== 1. CRAWL CATEGORY (product base) =========#
    # =====================================================#
    
    urls = [
        #Áo khoác
        "https://www.uniqlo.com/vn/vi/women/outerwear",
        #Áo thun, áo nỉ
        "https://www.uniqlo.com/vn/vi/women/t-shirts-sweat-and-fleece",
        #Ao len
        "https://www.uniqlo.com/vn/vi/women/sweaters-and-knitwear",
        #Áo sơ mi
        "https://www.uniqlo.com/vn/vi/women/shirts-and-blouses",
        #Quần
        "https://www.uniqlo.com/vn/vi/women/bottoms",
        #Váy, Đầm
        "https://www.uniqlo.com/vn/vi/women/skirts-and-dresses",
        #Đồ thể thao
        "https://www.uniqlo.com/vn/vi/women/sport-utility-wear",
        #Đồ mặc nhà
        "https://www.uniqlo.com/vn/vi/women/loungewear-and-homewear",

    ]

    product_base = []
    for url in urls:
        print("Crawling category:", url)
        product_base, images, categoriesID = crawl_category_products(driver, url)
        
        # Append ngay sau khi crawl xong category
        append_json("uniqlo_product_base.json", product_base)
        append_json("uniqlo_all_images.json", images)
    
        print(f"Category done: {len(product_base)} products added.")

    driver.quit()
    print(f"{len(urls)} categories crawled.")
