import requests
import os
import json

BASE_URL = "http://localhost:8000"

def test_product_flow():
    # 1. Create Product
    xml = """<?xml version="1.0" encoding="utf-8"?>
<dt_asset xmlns="http://digital-thread.re/dt_asset" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" schemaVersion="v31">
  <asset_global_id>https://digital-thread.re/kitech/prod_test1</asset_global_id>
  <id>prod_test1</id>
  <asset_kind>instance</asset_kind>
  <dt_elements xsi:type="dt_product">
    <element_id>prod_test1</element_id>
    <category>Machining Product</category>
    <display_name>Test Machining Product</display_name>
    <element_description>Result of machining mes_test2.</element_description>
    <its_id>PROD_001</its_id>
  </dt_elements>
</dt_asset>"""
    
    print("--- 1. Create Product ---")
    r1 = requests.post(f"{BASE_URL}/tools/create_product", json={"xml_string": xml})
    print(f"Status: {r1.status_code}")
    print(r1.text)

    # 2. Attach Product to Project
    print("\n--- 2. Attach Product to Project ---")
    payload2 = {
        "project_global_asset_id": "https://digital-thread.re/kitech/mes_test2",
        "project_asset_id": "mes_test2",
        "project_element_id": "mes_test2",
        "product_global_asset_id": "https://digital-thread.re/kitech/prod_test1",
        "product_asset_id": "prod_test1",
        "product_element_id": "prod_test1"
    }
    r2 = requests.post(f"{BASE_URL}/tools/attach_product_to_project", json=payload2)
    print(f"Status: {r2.status_code}")
    print(r2.text)

    # 3. Create a dummy result file and attach to Product
    print("\n--- 3. Upload and Attach Output to Product ---")
    dummy_file = "machining_log.txt"
    with open(dummy_file, "w") as f:
        f.write("Axis X: 10.2\nAxis Y: 5.4\nStatus: SUCCESS")
    
    payload3 = {
        "product_global_asset_id": "https://digital-thread.re/kitech/prod_test1",
        "product_asset_id": "prod_test1",
        "product_element_id": "prod_test1",
        "file_path": os.path.abspath(dummy_file),
        "ref_category": "Machining Log"
    }
    r3 = requests.post(f"{BASE_URL}/tools/upload_and_attach_to_product", json=payload3)
    print(f"Status: {r3.status_code}")
    print(r3.text)
    
    os.remove(dummy_file)

if __name__ == "__main__":
    test_product_flow()
