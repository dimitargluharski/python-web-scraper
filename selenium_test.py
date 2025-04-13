from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Настройки за headless браузър
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    event_url = "https://radamel.icu/reproductor/espn.php?width=700&height=438"
    print(f"🔍 Отваряме страницата: {event_url}")
    driver.get(event_url)

    # ⏳ Изчакваме родителския iframe
    outer_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )
    driver.switch_to.frame(outer_iframe)

    # ⏳ Сега изчакваме вътрешния iframe
    inner_iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )

    iframe_src = inner_iframe.get_attribute("src")
    print(f"✅ Вътрешен iframe src:\n{iframe_src}")

except Exception as e:
    print(f"❌ Грешка при извличане на iframe: {e}")

finally:
    driver.quit()
