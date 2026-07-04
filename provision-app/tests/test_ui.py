import os
import time
import socket
import shutil
import subprocess
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Check if browser is available in the environment to decide whether to skip tests
chrome_available = (
    shutil.which("google-chrome") is not None or 
    shutil.which("chromium-browser") is not None or 
    shutil.which("chromium") is not None
)

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

@pytest.fixture(scope="module")
def server_url():
    """Starts the FastAPI application in a background process on port 8082."""
    port = 8082
    db_file = "test_ui.db"
    
    # Clean old db if exists
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_file}",
        "ENV": "test"
    }
    
    # Launch uvicorn
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", str(port), "--host", "127.0.0.1"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    retries = 30
    server_ready = False
    while retries > 0:
        if is_port_open(port):
            server_ready = True
            break
        time.sleep(0.2)
        retries -= 1
        
    if not server_ready:
        proc.terminate()
        stdout, stderr = proc.communicate()
        raise RuntimeError(f"Server failed to start on port {port}. Stderr: {stderr.decode()}")
        
    yield f"http://127.0.0.1:{port}"
    
    # Teardown
    proc.terminate()
    proc.wait()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

@pytest.fixture(scope="module")
def driver():
    """Initializes headless Chrome web driver."""
    if not chrome_available:
        pytest.skip("Chrome/Chromium is not installed in this environment. Skipping Selenium UI tests.")
        
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1024")
    
    driver_obj = None
    try:
        service = Service(ChromeDriverManager().install())
        driver_obj = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        # Fallback to default path chromedriver if download fails or is pre-installed
        try:
            driver_obj = webdriver.Chrome(options=options)
        except Exception as inner_e:
            pytest.skip(f"Could not start ChromeDriver: {inner_e}")
            
    yield driver_obj
    
    if driver_obj:
        driver_obj.quit()


def test_ui_dashboard_page(driver, server_url):
    """Verifies that the dashboard loads successfully."""
    driver.get(server_url)
    time.sleep(1) # Wait for page rendering
    
    # Check title/header
    header = driver.find_element(By.TAG_NAME, "h2")
    assert "Dashboard" in header.text
    
    # Check widgets
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Spent This Month" in body_text
    assert "Monthly Direct Debits" in body_text
    assert "Quick Add Expense" in body_text


def test_ui_add_and_edit_expense(driver, server_url):
    """Verifies creating and editing an expense via the UI CRUD."""
    driver.get(f"{server_url}/expenses")
    time.sleep(1)
    
    # 1. Add new expense
    add_btn = driver.find_element(By.XPATH, "//button[contains(., 'Add Expense Entry')]")
    add_btn.click()
    time.sleep(0.5)
    
    # Fill in inline form
    desc_input = driver.find_element(By.NAME, "description")
    desc_input.send_keys("Selenium Tea Party")
    
    amount_input = driver.find_element(By.NAME, "amount")
    amount_input.clear()
    amount_input.send_keys("-15.45")
    
    # Submit form
    submit_btn = driver.find_element(By.XPATH, "//button[@title='Save']")
    submit_btn.click()
    time.sleep(1)
    
    # Assert item was added
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Selenium Tea Party" in body_text
    assert "-15.45" in body_text
    
    # 2. Edit the expense
    # Find the edit button for the newly added item
    # Since it is at the top of the table (swapped afterbegin)
    edit_buttons = driver.find_elements(By.XPATH, "//button[@title='Edit']")
    edit_buttons[0].click()
    time.sleep(0.5)
    
    # Modify amount
    amount_input = driver.find_element(By.NAME, "amount")
    amount_input.clear()
    amount_input.send_keys("-18.50")
    
    # Save edit
    submit_btn = driver.find_element(By.XPATH, "//button[@title='Save']")
    submit_btn.click()
    time.sleep(1)
    
    # Assert change occurred
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Selenium Tea Party" in body_text
    assert "-18.50" in body_text


def test_ui_bulk_edit_and_upload(driver, server_url):
    """Verifies that bulk provisioning edits can be executed."""
    driver.get(f"{server_url}/bulk-upload")
    time.sleep(1)
    
    # Select target month/year and submit bulk upload
    # Since mock rules were seeded on startup, there will be direct debits and lump sums listed.
    # Locate the first amount input field in bulk upload
    amount_inputs = driver.find_elements(By.XPATH, "//input[contains(@name, 'rule_amount_')]")
    assert len(amount_inputs) > 0
    
    # Modify the first rule's amount
    amount_inputs[0].clear()
    amount_inputs[0].send_keys("-175.00")
    
    # Click upload
    upload_btn = driver.find_element(By.XPATH, "//button[contains(., 'Execute Bulk Upload')]")
    upload_btn.click()
    time.sleep(1)
    
    # Verify success message and inserted items show up in results
    results_div = driver.find_element(By.ID, "upload-results")
    assert "Bulk Provisioning Completed!" in results_div.text
    assert "175.00" in results_div.text


def test_ui_add_scheduled_rule(driver, server_url):
    """Verifies adding a scheduled rule in the Admin settings."""
    driver.get(f"{server_url}/admin-settings")
    time.sleep(1)
    
    # Click Add Rule button
    add_btn = driver.find_element(By.XPATH, "//button[contains(., 'Add Scheduled Rule')]")
    add_btn.click()
    time.sleep(0.5)
    
    # Fill in details
    desc_input = driver.find_element(By.NAME, "description")
    desc_input.send_keys("Selenium Rent Charge")
    
    day_input = driver.find_element(By.NAME, "day_of_month")
    day_input.clear()
    day_input.send_keys("4")
    
    amount_input = driver.find_element(By.NAME, "amount")
    amount_input.clear()
    amount_input.send_keys("-1200.00")
    
    # Save the rule
    save_btn = driver.find_element(By.XPATH, "//button[@title='Save']")
    save_btn.click()
    time.sleep(1)
    
    # Check if the new rule exists in the rules table list
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Selenium Rent Charge" in body_text
    assert "1200.00" in body_text
