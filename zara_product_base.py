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
# HÀM ĐỢI LOAD SẢN PHẨM ỔN ĐỊNH
# =====================================================
def wait_until_products_loaded(driver, timeout=15, min_stable_time=1):
    previous_count = -1
    stable_start = time.time()

    while time.time() - stable_start < min_stable_time:
        products = driver.find_elements(By.CSS_SELECTOR, "li.product-grid-product")
        current_count = len(products)

        if current_count != previous_count:
            previous_count = current_count
            stable_start = time.time()  # reset timer khi số lượng thay đổi

        if time.time() - stable_start > min_stable_time:
            break

        if time.time() - stable_start > timeout:
            break
        time.sleep(0.3)

# =====================================================
# HÀM CRAWL SẢN PHẨM TRONG CATEGORY
# =====================================================
def crawl_category_products(driver, url):
    driver.get(url)
    
    #Load trang ổn định
    time.sleep(10)
    wait_until_products_loaded(driver,timeout=30)


    parsed_url = urlparse(url)
    categoriesID = parse_qs(parsed_url.query).get("v1", [""])[0] or parse_qs(parsed_url.query).get("v2", [""])[0]

    # ===== LẤY LIST ẢNH =====
    image_items = driver.find_elements(By.CSS_SELECTOR, "li.product-grid-product")

    # ===== LẤY LIST INFO (NAME + PRICE) =====
    info_items = driver.find_elements(By.CSS_SELECTOR, "li.product-grid-block-dynamic__product-info")

    product_list = []
    all_images = []

    # ===== GHÉP ẢNH + NAME + PRICE THEO CHỈ SỐ =====
    for idx in range(min(len(image_items), len(info_items))):

        product_img_block = image_items[idx]
        info_block = info_items[idx]

        # PRODUCT ID & KEY
        productID = product_img_block.get_attribute("data-productid")
        productKey = product_img_block.get_attribute("data-productkey")

        # ===== NAME =====
        try:
            name_el = info_block.find_element(By.CSS_SELECTOR, "a.product-grid-product-info__name h3")
            name = name_el.text.strip()
        except:
            name = None

        # ===== PRICE =====
        try:
            price_el = info_block.find_element(By.CSS_SELECTOR, "span.money-amount__main")
            price = price_el.text.strip()
        except:
            price = None

        # ===== IMAGE + ALT =====
        img_elements = product_img_block.find_elements(By.CSS_SELECTOR, "img.media-image__image")
        image_link = None
        alt = None
        if img_elements:
            image_link = img_elements[0].get_attribute("src")
            alt = img_elements[0].get_attribute("alt")

        if image_link:
            all_images.append({
                "product_id": productID,
                "image_url": image_link,
                "alt": alt
            })

        # ===== PRODUCT URL =====
        try:
            product_key_part = productKey.split("-")[0]
            product_url = f"https://www.zara.com/vn/vi/-p{product_key_part}.html?v1={productID}&v2={categoriesID}"
        except:
            product_url = None

        # ===== ADD TO BASE =====
        product_list.append({
            "product_id": productID,
            "product_key": productKey,
            "categoriesID": categoriesID,
            "name": name,
            "price": price,
            "image": {
                "image_link": image_link,
                "alt": alt
            },
            "url": product_url
        })

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
        "https://www.zara.com/vn/vi/woman-jackets-l1114.html?v1=2417772",
        "https://www.zara.com/vn/vi/woman-outerwear-l1184.html?v1=2419032",
        "https://www.zara.com/vn/vi/woman-outerwear-padded-l1195.html?v1=2419045",
        "https://www.zara.com/vn/vi/woman-blazers-l1055.html?v1=2420942",
        "https://www.zara.com/vn/vi/woman-dresses-l1066.html?v1=2420896",
        "https://www.zara.com/vn/vi/woman-tops-l1322.html?v1=2419940",
        "https://www.zara.com/vn/vi/woman-body-l1057.html?v1=2420490",
        "https://www.zara.com/vn/vi/woman-knitwear-l1152.html?v1=2420306",
        "https://www.zara.com/vn/vi/woman-jeans-l1119.html?v1=2419185",
        "https://www.zara.com/vn/vi/woman-trousers-l1335.html?v1=2420795",
        "https://www.zara.com/vn/vi/woman-shirts-l1217.html?v1=2420369",
        "https://www.zara.com/vn/vi/woman-tshirts-l1362.html?v1=2420417",
        "https://www.zara.com/vn/vi/woman-cardigans-sweaters-l8322.html?v1=2419844",
        "https://www.zara.com/vn/vi/woman-co-ords-l1061.html?v1=2420285",
        "https://www.zara.com/vn/vi/woman-skirts-l1299.html?v1=2420454",
        "https://www.zara.com/vn/vi/woman-sweatshirts-l1320.html?v1=2467842",
        "https://www.zara.com/vn/vi/woman-trousers-joggers-l1346.html?v1=2467843"
    ]
    product_base = []
    for url in urls:
        print("Crawling category:", url)
        product_base, images, categoriesID = crawl_category_products(driver, url)
        
        # Append ngay sau khi crawl xong category
        append_json("product_base.json", product_base)
        append_json("all_images.json", images)
    
        print(f"Category done: {len(product_base)} products added.")

    driver.quit()
    print(f"{len(urls)} categories crawled.")
