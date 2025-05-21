import time
import os
import json 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, InvalidArgumentException
import requests
from pystyle import Center, Colorate, Colors, Write, System
import datetime

# Nếu chưa cài colorama, chạy: pip install colorama
try:
    from colorama import init
    init(autoreset=True)
except ImportError:
    def init(*a, **k): pass

URL_FACEBOOK_LOGIN = "https://www.facebook.com"
VIA_FILE_PATH = "via.txt"
FB_PROFILE_SLUG_FOR_LOGIN_NAVIGATION = "me" 
is_reup_fb_logged_in = False

API_URL = "http://tiendeveloper.site/api.php"

def configure_main_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-automation','enable-logging'])
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-notifications")
    options.add_argument('--lang=en-US') 
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'en-US,en',
        "credentials_enable_service": False, 
        "profile.password_manager_enabled": False 
    })
    options.add_argument("--incognito")
    try:
        print("Đang khởi tạo WebDriver (chế độ ẩn danh)...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("WebDriver đã khởi tạo (chế độ ẩn danh).")
        return driver
    except Exception as e:
        print(f"Lỗi WebDriver: {e}")
        return None

def robust_click(driver, wait, by_type, locator_value, description, timeout=15, interaction_wait_time=1.5):
    element = None
    final_wait = WebDriverWait(driver, timeout)
    try:
        element = final_wait.until(EC.element_to_be_clickable((by_type, locator_value)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        time.sleep(0.5) 
        driver.execute_script("arguments[0].click();", element)
        print(f"Clicked '{description}' successfully via JS.")
        time.sleep(interaction_wait_time)
        return True
    except Exception:
        if element: 
            try:
                element.click()
                print(f"Clicked '{description}' successfully via direct click.")
                time.sleep(interaction_wait_time)
                return True
            except Exception as e_direct:
                print(f"Direct click for '{description}' also failed: {type(e_direct).__name__}")
    return False

def execute_facebook_cookie_login(driver, wait_medium, cookies_list):
    global is_reup_fb_logged_in
    if is_reup_fb_logged_in:
        print("Trần Anh Tú nói đăng nhập thành công (đã đăng nhập trước đó)")
        return True
    print("\nBắt đầu đăng nhập Facebook bằng cookie...")
    driver.get(f"{URL_FACEBOOK_LOGIN}/robots.txt") 
    time.sleep(0.5)
    driver.get(URL_FACEBOOK_LOGIN) 
    time.sleep(1)
    print(f"Đang thêm {len(cookies_list)} cookie vào trình duyệt...")
    for cookie_dict_orig in cookies_list:
        cookie_dict = cookie_dict_orig.copy()        
        if 'expiry' in cookie_dict and isinstance(cookie_dict['expiry'], float):
            cookie_dict['expiry'] = int(cookie_dict['expiry'])
        if 'expires' in cookie_dict: 
            if isinstance(cookie_dict['expires'], (int, float)):
                 cookie_dict['expiry'] = int(cookie_dict['expires'])
            del cookie_dict['expires']  
        if 'sameSite' in cookie_dict and cookie_dict['sameSite'] not in ['Strict', 'Lax', 'None', 'no_restriction', 'unspecified']:
            del cookie_dict['sameSite']
        for key_to_remove in ['storeId', 'session', 'hostOnly', 'id', 'SameSite']:
            if key_to_remove in cookie_dict:
                del cookie_dict[key_to_remove]
        if 'domain' in cookie_dict and cookie_dict['domain'] == "facebook.com":
             cookie_dict['domain'] = ".facebook.com"
        elif 'domain' not in cookie_dict:
             print(f"    Cảnh báo: Cookie '{cookie_dict.get('name')}' không có thuộc tính 'domain'. Sẽ thử thêm.")
        try:
            driver.add_cookie(cookie_dict)
        except InvalidArgumentException as e_cookie_invalid:
            print(f"    Lỗi InvalidArgumentException khi thêm cookie '{cookie_dict.get('name', 'N/A')}': {e_cookie_invalid}. Cookie data: {cookie_dict}")
        except Exception as e_cookie:
            print(f"    Lỗi chung khi thêm cookie '{cookie_dict.get('name', 'N/A')}': {type(e_cookie).__name__} - {e_cookie}. Cookie data: {cookie_dict}")
    print("Đã thêm cookies. Làm mới trang...")
    driver.refresh()
    time.sleep(max(5, wait_medium._timeout / 3)) 
    current_url_lower = driver.current_url.lower()
    print(f"URL sau khi làm mới và thêm cookie: {current_url_lower}")
    is_on_login_page_indicator = False
    try:
        if driver.find_element(By.XPATH, "//input[@name='email']").is_displayed() or \
           driver.find_element(By.XPATH, "//button[@name='login']").is_displayed():
            is_on_login_page_indicator = True
            print("Phát hiện các yếu tố của trang đăng nhập.")
    except: pass
    logged_in_element_xpath = "//a[@aria-label='Home' or @aria-label='Trang chủ'] | //div[@aria-label='Tạo bài viết' or @aria-label='Create post'] | //a[contains(@href, '/me/') or contains(@href, '/profile.php?id=')][descendant::img]"
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, logged_in_element_xpath)))
        print("Trần Anh Tú nói đăng nhập thành công (bằng cookie - tìm thấy yếu tố đăng nhập)")
        is_reup_fb_logged_in = True
        return True
    except TimeoutException:
        if "facebook.com" in current_url_lower and \
           not ("checkpoint" in current_url_lower or \
                "login" in current_url_lower or \
                "locked" in current_url_lower or \
                "challenge" in current_url_lower) and \
           not is_on_login_page_indicator:
            print("Trần Anh Tú nói đăng nhập thành công (bằng cookie - kiểm tra URL, không có dấu hiệu login/checkpoint)")
            is_reup_fb_logged_in = True
            return True
        else:
            print(f"LỖI - Đăng nhập bằng cookie không thành công. URL hiện tại: {driver.current_url}.")
            is_reup_fb_logged_in = False
            return False
    except Exception as e_login_cookie:
        print(f"Lỗi nghiêm trọng trong quá trình đăng nhập bằng cookie: {type(e_login_cookie).__name__} - {e_login_cookie}")
        is_reup_fb_logged_in = False
        return False

def click_report_option(driver, wait, option_text, step_description):
    print(f"Click tùy chọn: '{option_text}'...")
    normalized_option_text = option_text.lower()
    xpath_priority = f"//div[@role='dialog']//div[(@role='button' or @role='radio' or @role='menuitemradio' or @role='menuitem') and .//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{normalized_option_text}\")]]"
    xpath_fallback_ancestor = f"//div[@role='dialog']//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{normalized_option_text}\")]/ancestor::div[@role='button' or @role='radio' or @role='menuitemradio' or @role='menuitem'][1]"
    xpath_fallback_direct_text = f"//div[@role='dialog']//div[(@role='button' or @role='radio')][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{normalized_option_text}\")]"
    if robust_click(driver, wait, By.XPATH, xpath_priority, step_description): return True
    if robust_click(driver, wait, By.XPATH, xpath_fallback_ancestor, f"{step_description} (fallback ancestor)"): return True
    if robust_click(driver, wait, By.XPATH, xpath_fallback_direct_text, f"{step_description} (fallback direct text)"): return True
    print(f"Lỗi: Không tìm thấy hoặc click được '{option_text}'.")
    return False

def click_dialog_action(driver, wait, action_text_in_span=None, aria_label_for_button=None, description="Hành động dialog"):
    xpath = ""
    description_to_use = description
    if aria_label_for_button:
        normalized_aria_label = aria_label_for_button.lower()
        xpath = f"//div[@role='dialog']//div[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{normalized_aria_label}\") and @role='button']"
        description_to_use = f"{description} (aria-label: {aria_label_for_button})"
    elif action_text_in_span:
        normalized_action_text = action_text_in_span.lower()
        xpath = f"//div[@role='dialog']//div[@role='button'][.//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{normalized_action_text}\")]]"
        description_to_use = f"{description} (text: {action_text_in_span})"
    else:
        print(f"Lỗi: Cần action_text_in_span hoặc aria_label_for_button cho '{description}'.")
        return False
    print(f"Click '{description_to_use}'...")
    if not robust_click(driver, wait, By.XPATH, xpath, description_to_use):
        if action_text_in_span: 
            xpath_simple_button = f"//div[@role='dialog']//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{action_text_in_span.lower()}\")]"
            if robust_click(driver, wait, By.XPATH, xpath_simple_button, f"{description_to_use} (fallback button)"):
                return True
        print(f"Lỗi: Không tìm thấy hoặc click được '{description_to_use}'.")
        return False
    return True

def open_report_dialog(driver, wait):
    print("Mở menu tùy chọn (ba chấm)...")
    three_dots_xpath_1 = "//div[@aria-label='Profile settings see more options'][@role='button']"
    three_dots_xpath_2 = "//div[@aria-label='Tùy chọn khác' or @aria-label='More options' or translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='profile actions'][@role='button']" # Fallback
    if not robust_click(driver, wait, By.XPATH, three_dots_xpath_1, "Nút ba chấm (tùy chọn profile)"):
        if not robust_click(driver, wait, By.XPATH, three_dots_xpath_2, "Nút ba chấm (fallback)"):
            print("Lỗi: Không tìm thấy hoặc click được nút ba chấm.")
            return False
    print("Click 'Report profile'...")
    report_profile_xpath = "//div[@role='menuitem'][.//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'report profile')]]"
    if not robust_click(driver, wait, By.XPATH, report_profile_xpath, "Tùy chọn 'Report profile'"):
        print("Lỗi: Không tìm thấy hoặc click được 'Report profile'.")
        return False
    return True

def perform_report_sequence(driver, wait, options_to_click_config):
    if not open_report_dialog(driver, wait):
        print("Không mở được dialog báo cáo. Thử đóng dialog hiện có (nếu có) và thử lại.")
        try:
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            close_button_xpath = "(//div[@role='dialog']//div[@aria-label='Close' or @aria-label='Đóng' or @aria-label='close' or translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='close'])[1]"
            close_buttons = driver.find_elements(By.XPATH, close_button_xpath)
            if close_buttons:
                robust_click(driver, WebDriverWait(driver,2), By.XPATH, close_button_xpath, "Nút đóng dialog", interaction_wait_time=0.5)
                time.sleep(1)
        except: pass 
        if not open_report_dialog(driver, wait): 
            return False 
    for item_config in options_to_click_config:
        click_type = item_config.get("type", "option") 
        if click_type == "option":
            option_text = item_config.get("text")
            description = item_config.get("desc")
            if not option_text or not description:
                print(f"Lỗi cấu hình cho tùy chọn: {item_config}")
                return False
            if not click_report_option(driver, wait, option_text, description):
                return False
        elif click_type == "action":
            action_text = item_config.get("text") 
            aria_label = item_config.get("aria_label") 
            description = item_config.get("desc")
            if not description or (not action_text and not aria_label) :
                print(f"Lỗi cấu hình cho hành động: {item_config}")
                return False
            if not click_dialog_action(driver, wait, action_text_in_span=action_text, aria_label_for_button=aria_label, description=description):
                return False
        else:
            print(f"Loại click không xác định: {click_type} trong {item_config}")
            return False
    print("Hoàn thành một chuỗi báo cáo.")
    return True

def main():
    cookies_list = []
    if not os.path.exists(VIA_FILE_PATH):
        print(f"Lỗi: Không tìm thấy file {VIA_FILE_PATH}. Vui lòng tạo file chứa cookie.")
        return
    try:
        with open(VIA_FILE_PATH, "r", encoding="utf-8") as f:
            cookie_line_from_file = f.readline().strip()
            if not cookie_line_from_file:
                print(f"Lỗi: File {VIA_FILE_PATH} rỗng.")
                return
            if cookie_line_from_file.startswith("[") and cookie_line_from_file.endswith("]"):
                try:
                    cookies_list = json.loads(cookie_line_from_file)
                    if not isinstance(cookies_list, list):
                        print(f"Lỗi: Dữ liệu cookie JSON trong {VIA_FILE_PATH} không phải là một list.")
                        cookies_list = []
                    else:
                        print(f"Đã parse {len(cookies_list)} cookie từ chuỗi JSON.")
                except json.JSONDecodeError:
                    print(f"Không thể parse dòng đầu tiên trong {VIA_FILE_PATH} như JSON. Sẽ thử parse như chuỗi key=value;.")
                    cookies_list = [] 
            if not cookies_list:
                print(f"Đang thử parse cookie từ định dạng key=value; ...")
                raw_cookie_parts = cookie_line_from_file.split(';')
                temp_cookies_list = []
                for part in raw_cookie_parts:
                    part = part.strip()
                    if not part:
                        continue
                    if '=' in part:
                        name, value = part.split('=', 1)
                        name = name.strip()
                        value = value.strip()                     
                        cookie_dict = {
                            'name': name,
                            'value': value,
                            'domain': '.facebook.com', 
                            'path': '/',
                            'secure': True 
                        }
                        if name in ['xs', 'fr', 'sb', 'datr']:
                            cookie_dict['httpOnly'] = True
                        else:
                            cookie_dict['httpOnly'] = False
                        temp_cookies_list.append(cookie_dict)
                    else:
                        print(f"Cảnh báo: Phần cookie không hợp lệ (thiếu '='): '{part}'")
                cookies_list = temp_cookies_list

            if not cookies_list:
                print(f"Lỗi: Không thể parse được cookie nào từ {VIA_FILE_PATH}. Vui lòng kiểm tra nội dung file (cần là JSON list hoặc chuỗi key=value;).")
                return
            else:
                 print(f"Đã parse/tải tổng cộng {len(cookies_list)} cookie.")
    except Exception as e_file:
        print(f"Lỗi khi đọc hoặc xử lý file cookie {VIA_FILE_PATH}: {e_file}")
        return
    print("Trần Anh Tú hỏi cưng muốn dame acc nào? Link đi: ", end="")
    target_url = input()
    if not target_url.startswith("https://www.facebook.com"):
        print("Link không hợp lệ. Phải bắt đầu bằng https://www.facebook.com")
        return
    driver = configure_main_driver()
    if not driver:
        return
    wait_medium = WebDriverWait(driver, 20) 
    wait_long = WebDriverWait(driver, 45)   
    if not execute_facebook_cookie_login(driver, wait_medium, cookies_list):
        print("Đăng nhập Facebook bằng cookie thất bại. Kết thúc.")
        driver.quit()
        return
    final_report_steps_config = [
        {"type": "action", "aria_label": "Submit", "desc": "Nút Submit"},
        {"type": "action", "text": "Next", "desc": "Nút Next"},
        {"type": "action", "text": "Done", "desc": "Nút Done"}
    ]
    report_flows_config = [
        [{"type": "option", "text": "Fake account", "desc": "Tùy chọn Fake Account"}] + final_report_steps_config,
        [{"type": "option", "text": "Fake profile", "desc": "Tùy chọn Fake Profile (old)"}, {"type": "option", "text": "They're not a real person", "desc": "Tùy chọn 'They're not a real person'"}] + final_report_steps_config,
        [{"type": "option", "text": "Bullying, harassment or abuse", "desc": "Bullying/Harassment/Abuse"}, {"type": "option", "text": "Bullying or harassment", "desc": "Bullying or harassment option"}, {"type": "option", "text": "I don't know them", "desc": "I don't know them option"}] + final_report_steps_config,
        [{"type": "option", "text": "Violent, hateful or disturbing content", "desc": "Violent/Hateful Content"}, {"type": "option", "text": "Promoting hate", "desc": "Promoting hate option"}, {"type": "option", "text": "It represents an organized hate group", "desc": "Organized hate group"}] + final_report_steps_config,
        [{"type": "option", "text": "Adult content", "desc": "Adult Content option"}, {"type": "option", "text": "My nude images have been shared", "desc": "My nude images shared"}] + final_report_steps_config,
        [{"type": "option", "text": "Bullying, harassment or abuse", "desc": "Bullying/Harassment/Abuse (flow 5)"}, {"type": "option", "text": "Seems like sexual exploitation", "desc": "Sexual exploitation option"}] + final_report_steps_config,
    ]
    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n--- Vòng lặp báo cáo thứ {loop_count} ---")
        try:
            print(f"Điều hướng tới: {target_url}")
            driver.get(target_url)
            time.sleep(5)
        except Exception as nav_e:
            print(f"Lỗi khi điều hướng tới {target_url}: {nav_e}.")
            if loop_count > 1: 
                print("Trần Anh Tú nói rằng link đã die (lỗi điều hướng)")
                break
            print("Sẽ thử lại sau 10 giây..."); time.sleep(10); continue
        unavailable_xpath = "//div[contains(@class, 'x1ifrov1')]//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"this content isn't available at the moment\")] | //h2[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"this page isn't available\")]"
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            if driver.find_elements(By.XPATH, unavailable_xpath):
                print("Trần Anh Tú nói tài khoản này không hoạt động!!")
                break 
        except Exception as e_check:
            print(f"Lỗi khi kiểm tra tài khoản không hoạt động (có thể tạm thời): {e_check}")
        print("Tài khoản có vẻ vẫn hoạt động. Bắt đầu các chuỗi báo cáo...")
        for i, flow_step_config in enumerate(report_flows_config):
            print(f"\nThực hiện chuỗi báo cáo {i+1}/{len(report_flows_config)}...")
            current_page_url_before_report = driver.current_url
            if target_url not in current_page_url_before_report : 
                print(f"Đang ở URL {current_page_url_before_report}, không phải target. Điều hướng lại về {target_url}")
                try: driver.get(target_url); time.sleep(3)
                except Exception as nav_e2:
                     print(f"Lỗi điều hướng lại về {target_url}: {nav_e2}. Bỏ qua flow này."); continue 
            if not perform_report_sequence(driver, wait_medium, flow_step_config):
                print(f"Chuỗi báo cáo {i+1} thất bại. Thử refresh và điều hướng lại.")
                try: 
                    print("Đóng dialog có thể đang mở bằng ESCAPE...")
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                    driver.get(target_url)
                    time.sleep(3)
                except Exception as e_reset:
                    print(f"Lỗi khi cố gắng reset trạng thái: {e_reset}")
            else:
                print(f"Hoàn thành chuỗi báo cáo {i+1}.")
            time.sleep(3) 
        print("Đã hoàn thành tất cả các chuỗi báo cáo cho vòng lặp này. Reload trang...")
        try: driver.refresh(); time.sleep(5) 
        except Exception as refresh_e:
            print(f"Lỗi khi reload trang: {refresh_e}")
            print("Trần Anh Tú nói rằng link đã die (lỗi reload)"); break
    print("Kết thúc chương trình.")
    driver.quit()

def request_mac(mac):
    try:
        requests.post(API_URL, data={"mac": mac})
    except Exception as e:
        Write.Print(f"[!] Không thể gửi MAC lên server: {e}\n", Colors.red_to_yellow, interval=0.01)

def check_key(key):
    try:
        data = requests.get("https://www.tiendeveloper.site/auth_requests.json").json()
        for item in data:
            if item.get("key") == key:
                # Check status
                if item.get("status") not in ["approved", "active"]:
                    return {"success": False, "reason": "Chưa được duyệt"}
                # Check expire
                expire_at = item.get("expire_at")
                if expire_at:
                    now = datetime.datetime.now()
                    try:
                        expire_dt = datetime.datetime.strptime(expire_at, "%Y-%m-%d %H:%M:%S")
                    except:
                        expire_dt = datetime.datetime.strptime(expire_at, "%Y-%m-%d %H:%M")
                    if now > expire_dt:
                        return {"success": False, "reason": "Hết hạn"}
                return {
                    "success": True,
                    "key": item.get("key"),
                    "status": item.get("status"),
                    "expire_at": item.get("expire_at")
                }
        return {"success": False, "reason": "Không tìm thấy key"}
    except Exception as e:
        return {"success": False, "reason": str(e)}

def banner():
    text = '''
╔════════════════════════════════════════════════════════════╗
██████╗  █████╗ ███╗   ███╗███████╗
██╔══██╗██╔══██╗████╗ ████║██╔════╝
██║  ██║███████║██╔████╔██║█████╗  
██║  ██║██╔══██║██║╚██╔╝██║██╔══╝  
██████╔╝██║  ██║██║ ╚═╝ ██║███████╗
╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝

   Tool Dame NOT X Mạo Danh

Liên hệ: Tele @cithinga | Zalo: 0942792489
Tool Được Code Bởi Trần Anh Tú Và Tiến Developer
╚════════════════════════════════════════════════════════════╝
'''
    System.Clear()
    for line in text.splitlines():
        Write.Print(Center.XCenter(line) + "\n", Colors.red_to_yellow, interval=0.002)
    Write.Print("\n", Colors.red_to_yellow, interval=0.01)

def show_key_info(info):
    # Xác định trạng thái
    status = info.get('status', '')
    if status == 'approved':
        status_str = 'Active :yes'
    else:
        status_str = 'No'
    # Vẽ khung hình chữ nhật lớn
    Write.Print("\n" + Center.XCenter("╔" + "═"*50 + "╗") + "\n", Colors.red_to_yellow, interval=0.001)
    Write.Print(Center.XCenter(f"║   Key: {info.get('key', ''):<40}║") + "\n", Colors.red_to_yellow, interval=0.001)
    Write.Print(Center.XCenter(f"║   Trạng thái: {status_str:<33}║") + "\n", Colors.red_to_yellow, interval=0.001)
    Write.Print(Center.XCenter(f"║   Hạn dùng: {info.get('expire_at', ''):<36}║") + "\n", Colors.red_to_yellow, interval=0.001)
    Write.Print(Center.XCenter("╚" + "═"*50 + "╝") + "\n", Colors.red_to_yellow, interval=0.001)

if __name__ == "__main__":
    banner()
    mac = "00:11:22:33:44:55"  # Thay bằng MAC thực tế nếu muốn tự động lấy
    key = None
    key_info = None
    # Thử đọc thông tin key từ file lưu trước đó
    try:
        with open("last_key.txt", "r", encoding="utf-8") as f:
            key = f.read().strip()
        with open("last_key_info.json", "r", encoding="utf-8") as f:
            key_info = json.load(f)
    except Exception:
        pass

    if not key:
        request_mac(mac)
        key = Write.Input("Nhập key đã được admin cấp: ", Colors.red_to_yellow, interval=0.01).strip()
        try:
            with open("last_key.txt", "w", encoding="utf-8") as f:
                f.write(key)
        except Exception:
            pass

    # Kiểm tra key
    result = check_key(key)
    if result.get('success'):
        # Lưu thông tin key vào file
        try:
            with open("last_key_info.json", "w", encoding="utf-8") as f:
                json.dump(result, f)
        except Exception:
            pass
        show_key_info(result)
        Write.Print("\n[✔] Key hợp lệ! Bạn có thể sử dụng tool.\n", Colors.green_to_cyan, interval=0.01)
        main()
    else:
        Write.Print(f"\n[✘] Key không hợp lệ hoặc đã hết hạn!\n", Colors.red_to_yellow, interval=0.01)
        exit(1)
