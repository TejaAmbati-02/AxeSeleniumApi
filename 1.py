import os
from pathlib import Path
from urllib.parse import urlparse
from selenium import webdriver
from axe_selenium_python import Axe
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException


def run_accessibility_test(url, options):
    driver = webdriver.Chrome(options=options)

    # Set a longer script timeout
    driver.set_script_timeout(60)  # Increase to 60 seconds

    try:
        driver.get(url)

        # Wait for the page to be fully loaded
        WebDriverWait(driver, 60).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete")

        axe = Axe(driver)
        axe.inject()

        # Run Axe script
        results = axe.run()
    except TimeoutException as te:
        print(f"Timeout while processing {url}: {str(te)}")
        results = None
    except WebDriverException as we:
        print(f"WebDriverException while processing {url}: {str(we)}")
        results = None
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        results = None
    finally:
        driver.quit()

    return results


def generate_json_filename(url, index, scenario):
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc.replace(".", "_")

    if index > 0:
        return f"{domain_name}_{index + 1}_{scenario}_results.json"
    else:
        return f"{domain_name}_{scenario}_results.json"


# Set up script folder and find Excel files
script_folder = Path(__file__).parent
excel_files = [file for file in os.listdir(script_folder) if file.endswith('.xlsx')]

if not excel_files:
    raise FileNotFoundError("No Excel File Found in the Script Folder.")

# Use the first Excel file found
excel_file_path = script_folder / excel_files[0]

# Read URLs from Excel file
df = pd.read_excel(excel_file_path)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

# Iterate through URLs and perform accessibility tests
for index, row in df.iterrows():
    url = row['URL']

    try:
        results = run_accessibility_test(url, options=chrome_options)

        if results is not None:
            # Separate results into scenarios
            for scenario in ['inapplicable', 'incomplete', 'passes', 'violations']:
                scenario_results = results.get(scenario, [])

                # Generate JSON file name based on the domain, index, and scenario
                output_json_file = generate_json_filename(url, index, scenario)

                # Save scenario-specific results to JSON file
                with open(output_json_file, 'w') as json_file:
                    json.dump(scenario_results, json_file, indent=2)

                print(f"{scenario.capitalize()} results for {url} have been saved to {output_json_file}")
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")