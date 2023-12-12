from flask import Flask, jsonify, request
import os
from pathlib import Path
from urllib.parse import urlparse
from selenium import webdriver
from axe_selenium_python import Axe
from selenium.webdriver.chrome.options import Options
import pandas as pd
import json
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def run_accessibility_test(url, options):
    driver = webdriver.Chrome(options=options)
    driver.set_script_timeout(30)
    driver.get(url)
    axe = Axe(driver)
    axe.inject()
    results = axe.run()
    driver.quit()
    return results

def generate_json_filename(url, index):
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc.replace(".", "_")

    if index > 0:
        return f"{domain_name}_{index + 1}_accessibility_results.json"
    else:
        return f"{domain_name}_accessibility_results.json"

@app.route('/run_accessibility_test', methods=['POST'])
def api_run_accessibility_test():
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the uploaded file to the server
    file_path = Path(__file__).parent / file.filename
    file.save(file_path)

    # Read URLs from the Excel file
    df = pd.read_excel(file_path)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    results_list = []

    # Iterate through URLs and perform accessibility tests
    for index, row in df.iterrows():
        url = row['URL']
        results = run_accessibility_test(url, options=chrome_options)
        output_json_file = generate_json_filename(url, index)

        with open(output_json_file, 'w') as json_file:
            json.dump(results, json_file, indent=2)

        results_list.append({
            "url": url,
            "results_file": output_json_file
        })

    return jsonify({"results": results_list})

if __name__ == '__main__':
    app.run(debug=True)