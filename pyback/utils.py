import requests
import re
from urllib.parse import urlparse
import whois


def is_valid_url(url):
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        domain = result.netloc
        if len(domain) > 253 or '..' in domain:
            return False
        if re.search(r'[^\x00-\x7F]', url):
            return False
        return True
    except ValueError:
        return False

def clean_url(url):
    return re.sub(r'[^\x00-\x7F]+', '', url)

def ensure_url_scheme(url):
    return 'https://' + url if not url.startswith(('http://', 'https://')) else url

def get_domain_age(domain):
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        expiration_date = w.expiration_date
        registrant_name = w.get('name', 'Unknown')

        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]

        if creation_date is None or expiration_date is None:
            return None, None, None, registrant_name

        domain_age_days = (expiration_date - creation_date).days
        return creation_date, expiration_date, domain_age_days, registrant_name
    except Exception as e:
        print(f"Error retrieving WHOIS information for {domain}: {e}")
        return None, None, None, 'Unknown'

# 도메인 추출 함수
def extract_domain_without_tld(url: str) -> str:
    parsed_url = urlparse(url.rstrip("/"))  # URL 파싱 후 마지막 '/' 제거
    domain = parsed_url.netloc  # netloc에서 도메인 추출
    if domain.startswith("www."):  # "www." 제거
        domain = domain[4:]
    # TLD 제거 (마지막 '.' 기준으로 분리)
    domain_parts = domain.split('.')
    if len(domain_parts) > 1:
        return domain_parts[-2]  # TLD 앞의 메인 도메인 반환
    return domain  # TLD 제거 불가능하면 원본 반환

# MongoDB에서 저장된 URL의 도메인 추출 및 비교
def is_url_in_collection(url: str, collection) -> bool:
    domain_to_check = extract_domain_without_tld(url)  # 입력 URL에서 도메인 추출
    # MongoDB에서 저장된 모든 URL에 대해 도메인 추출 후 비교
    for entry in collection.find():
        stored_url = entry.get("url", "")
        stored_domain = extract_domain_without_tld(stored_url)  # 저장된 URL에서 도메인 추출
        if domain_to_check == stored_domain:
            return True
    return False


def get_country_by_ip(ip_address):
    """IP 주소로부터 국가 정보를 반환"""
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/")
        if response.status_code == 200:
            return response.json().get("country_name", "Unknown")
        return "Unknown"
    except requests.RequestException:
        return "Unknown"

def get_user_country():
    """사용자의 IP 및 국가 정보 반환"""
    try:
        response = requests.get("https://ipapi.co/json/")
        if response.status_code == 200:
            user_data = response.json()
            user_ip = user_data.get("ip", "Unknown")
            user_country = user_data.get("country_name", "Unknown")
            return user_ip, user_country
        return "Unknown", "Unknown"
    except requests.RequestException:
        return "Unknown", "Unknown"

def is_obfuscated_script(script_content):
    """JavaScript 난독화 여부를 확인"""
    return bool(re.search(r"[a-zA-Z$_]\s*=\s*function\s*\(.*\)", script_content))