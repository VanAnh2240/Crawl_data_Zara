import json

with open("hm_product_base.json", "r", encoding="utf-8") as f:
    data = json.load(f)

seen = set()
unique_data = []
for item in data:
    if item['product_id'] not in seen:
        unique_data.append(item)
        seen.add(item['product_id'])

with open("hm_product_base_1.json", "w", encoding="utf-8") as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=2)

print("filtered hm_product_base_1.json")
