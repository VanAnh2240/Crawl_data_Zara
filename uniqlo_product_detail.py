import json
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
    wait = WebDriverWait(driver, 10)
    
    # ===== DESCRIPTION =====
    description = None
    try:
        desc_el = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.er-description"))
        )
        
        desc_feature_lines = []
        # Lấy phần Features nếu có
        feature_elements = desc_el.find_elements(By.CSS_SELECTOR, "section[data-test='features-accordion']")
        if feature_elements:
            desc_feature_lines = [
                " ".join(line.strip().split()) 
                for line in feature_elements[0].get_attribute("innerText").splitlines() 
                if line.strip()
            ]
        
        desc_overview_lines = []
        # Lấy phần Overview nếu có
        overview_elements = desc_el.find_elements(By.CSS_SELECTOR, "div[data-test='overview-accordion-content']")
        if overview_elements:
            desc_overview_lines = [
                " ".join(line.strip().split())
                for line in overview_elements[0].get_attribute("innerText").splitlines() 
                if line.strip()
            ]

        # Kết hợp 2 phần
        all_lines = desc_feature_lines + desc_overview_lines
        if all_lines:
            description = "\n".join(all_lines)

    except Exception as e:
        print("Error description:", e)

    
    # ===== COMPOSITION =====
    composition = None
    try:
        # Click vào accordion để expand
        accordion_head = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-test='material-accordion'] div.er-accordion__head button"))
        )
        driver.execute_script("arguments[0].click();", accordion_head)

        # Chờ nội dung hiện ra
        composition_el = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div[data-test='material-accordion'] div.er-accordion__content")
            )
        )

        # Lấy dòng Thân: …
        dd_elements = composition_el.find_elements(By.CSS_SELECTOR, "dd.fr-definition-list-description")
        composition = dd_elements[0].text.strip()
        
    except Exception as e:
        print("Error composition:", e)

        
    # ===== EXTRA IMAGES =====
    extra_images = []
    try:
        extra_img_elements = driver.find_elements(By.CSS_SELECTOR, "div.media-gallery--ec-renewal--grid img")
        for img in extra_img_elements:
            alt = img.get_attribute("alt")
            src = img.get_attribute("src")
            if alt != "image-0" and src:
                extra_images.append(src)
    except Exception as e:
        print("Error extra images:", e)


    # ===== COLORS & MAIN IMAGE =====
    colors_data = []
    try:
        color_wrappers = WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "div.color-picker-wrapper div.fr-chip-wrapper-er")
        )

        for wrapper in color_wrappers:
            label = wrapper.find_element(By.CSS_SELECTOR, "label.fr-chip-label.color")
            color_name = wrapper.get_attribute("data-test")
            driver.execute_script("arguments[0].click();", label)

            # Đợi main image đổi
            main_img_el = wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "div.ec-renewal-image-wrapper img[alt='image-0']"))
            main_img = main_img_el.get_attribute("src")

            colors_data.append({
                "color_name": color_name,
                "main_image": main_img
            })
    except Exception as e:
        print("Error colors/main images:", e)


    # ===== RETURN DATA =====
    return {
        "product_id": product_id,
        "description": description,
        "composition": composition,
        "extra_images": extra_images,
        "colors": colors_data
    }
    

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__": 
    driver = init_driver()

    # =====================================================#
    # ========== Crawl detail từng sản phẩm  ============#
    # =====================================================#

    with open("uniqlo_product_base.json", "r", encoding="utf-8") as f:
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
        if (idx + 1) % 1 == 0:
            append_json("uniqlo_product_detail.json", detail_output)
            detail_output = [] 
    
    # Ghi phần còn lại
    if detail_output:
        append_json("uniqlo_product_detail.json", detail_output)

    driver.quit()
    print(f"{len(products)} products detail crawled.")
