import requests
from bs4 import BeautifulSoup
import socket
import tldextract
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import dns.resolver
from utils import clean_url, is_valid_url, ensure_url_scheme, get_domain_age, get_country_by_ip, get_user_country, is_obfuscated_script

class Crawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")

    def crawl_website_with_selenium(self, url):
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
            driver.get(url)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            hidden_iframes = sum(
                1 for iframe in iframes if iframe.get_attribute('style') == 'display:none;' or iframe.get_attribute('width') == '0'
            )

            content_size = len(page_source)
            driver.quit()

            return hidden_iframes, content_size
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None, None

    def analyze_website(self, url):
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
            dynamic_analysis = {
                'redirection_count': 0,
                'external_domain_requests': 0,
                'malicious_file_downloads': 0,
                'script_execution_count': 0,
                'iframe_present': False,
                'ajax_calls': 0,
                'cookie_settings': 0
            }

            driver.set_page_load_timeout(10)
            driver.get(url)

            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            dynamic_analysis['iframe_present'] = len(iframes) > 0

            dynamic_analysis['ajax_calls'] = len(
                driver.find_elements(By.XPATH, "//script[contains(text(), 'XMLHttpRequest')]")
            )
            if 'document.cookie' in driver.page_source:
                dynamic_analysis['cookie_settings'] += 1

            dynamic_analysis['script_execution_count'] = len(driver.find_elements(By.TAG_NAME, 'script'))
        except Exception as e:
            print(f"Error analyzing {url}: {e}")
        finally:
            driver.quit()

        return dynamic_analysis

    def crawl_website(self, url):
        url = clean_url(url)
        if not is_valid_url(url):
            print(f"Invalid URL: {url}. Skipping this URL.")
            return None

        try:
            url = ensure_url_scheme(url)
            start_time = time.time()

            try:
                response = requests.get(url, headers=self.headers, timeout=15, allow_redirects=False)
            except UnicodeError as e:
                print(f"Skipping URL due to UnicodeError: {url}. Error: {e}")
                return None

            redirect_count = 0
            final_url = url
            if 300 <= response.status_code < 400:
                final_url = response.headers.get('Location', url)
                redirect_count = 1

            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            loading_time = time.time() - start_time

            parsed_url = tldextract.extract(url)
            domain = parsed_url.domain + '.' + parsed_url.suffix

            try:
                ip_address = socket.gethostbyname(domain)
                country = get_country_by_ip(ip_address)
            except socket.error:
                ip_address = None
                country = 'Unknown'

            user_ip, user_country = get_user_country()
            countries_match = 'Yes' if user_country == country else 'No'

            creation_date, expiration_date, domain_age, registrant_name = get_domain_age(domain)
            subdomain_count = len(parsed_url.subdomain.split('.')) if parsed_url.subdomain else 0
            hidden_iframe_count, content_size = self.crawl_website_with_selenium(url)

            script_tags = soup.find_all('script')
            total_script_length = sum(len(script.text) for script in script_tags)
            obfuscated_script_length = sum(len(script.text) for script in script_tags if is_obfuscated_script(script.text))
            obfuscation_ratio = (obfuscated_script_length / total_script_length) if total_script_length > 0 else 0
            is_obfuscated = any(is_obfuscated_script(script.text) for script in script_tags)
            script_count = len(script_tags)

            meta_redirect = len(soup.find_all('meta', attrs={"http-equiv": "refresh"}))
            window_redirect = any('window.location' in script.text for script in script_tags)
            ajax_calls = sum(1 for script in script_tags if 'XMLHttpRequest' in script.text or 'fetch' in script.text)
            ssl_used = url.startswith('https')
            cookie_access = any('document.cookie' in script.text for script in script_tags)
            favicon = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
            x_frame_options = response.headers.get('X-Frame-Options', None)

            try:
                spf_records = dns.resolver.resolve(domain, 'TXT')
                spf = any("v=spf1" in str(record) for record in spf_records)
            except Exception:
                spf = False

            try:
                txt_records = dns.resolver.resolve(domain, 'TXT')
                txt = len(txt_records) > 0
            except Exception:
                txt = False

            html_tag = soup.find("html")
            lang = bool(html_tag.get("lang")) if html_tag else False

            images = soup.find_all("img")
            texts = soup.get_text().strip().split()
            text_image_ratio = len(texts) / len(images) if images else len(texts)

            dynamic_analysis = self.analyze_website(url)

            result = {
                'URL': url,
                'IP Address': ip_address,
                'Country': country,
                'User Country': user_country,
                'Countries Match': countries_match,
                'Domain Age (days)': domain_age,
                'Creation Date': creation_date,
                'Expiration Date': expiration_date,
                'Registrant Name': registrant_name,
                'Subdomain Count': subdomain_count,
                'Hidden Iframe Count': hidden_iframe_count,
                'Total Script Length': total_script_length,
                'Obfuscated Script Length': obfuscated_script_length,
                'Obfuscation Ratio': obfuscation_ratio,
                'Is Obfuscated': is_obfuscated,
                'Script Count': script_count,
                'Meta Redirect': meta_redirect,
                'Window Location Redirect': window_redirect,
                'AJAX Call Count': ajax_calls,
                'SSL Used': ssl_used,
                'Cookie Access': cookie_access,
                'Loading Time (s)': loading_time,
                'Content Size (bytes)': content_size,
                'Redirect Count': redirect_count,
                'Final URL': final_url,
                'redirection_count': dynamic_analysis['redirection_count'],
                'external_domain_requests': dynamic_analysis['external_domain_requests'],
                'malicious_file_downloads': dynamic_analysis['malicious_file_downloads'],
                'script_execution_count': dynamic_analysis['script_execution_count'],
                'iframe_present': dynamic_analysis['iframe_present'],
                'ajax_calls_dynamic': dynamic_analysis['ajax_calls'],
                'cookie_settings': dynamic_analysis['cookie_settings'],
                'favicon': bool(favicon),
                'x frame option': bool(x_frame_options),
                'spf': spf,
                'txt': txt,
                'lang': lang,
                'img and texts': text_image_ratio,
            }
            return result
        except Exception as e:
            print(f"Error during crawling {url}: {e}")
            return None
