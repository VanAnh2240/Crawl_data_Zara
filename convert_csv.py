import json
import pandas as pd
from pandas import json_normalize

# Đường dẫn file JSON
input_file = "uniqlo_product_base.json"
output_file = "uniqlo_product_base.csv"

# Load JSON
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Chuẩn hóa: đảm bảo mỗi product là dict và có các key cần thiết
cleaned_data = []
for item in data:
    if not isinstance(item, dict):
        continue  # bỏ qua nếu item là None hoặc không phải dict
    item.setdefault("images", [])
    item.setdefault("colors", [])
    item.setdefault("composition", "")
    item.setdefault("product_id", "")
    item.setdefault("description", "")
    cleaned_data.append(item)

# Flatten JSON
df = json_normalize(
    cleaned_data,
    record_path="images",
    meta=["product_id", "description", "colors", "composition"],
    errors="ignore"
)

# Xuất CSV
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print("Done! Saved:", output_file)
