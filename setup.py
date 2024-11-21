from setuptools import setup, find_packages

setup(
    name="pyback",                     # 패키지 이름 (사용자가 설치 시 사용할 이름)
    version="1.0.0",                   # 패키지 버전
    packages=find_packages(),          # 포함할 패키지 자동 탐지
    include_package_data=True,         # 추가 데이터 파일 포함 (예: 모델 파일)
    zip_safe=False,                    # .egg 대신 .whl 설치를 위해 False로 설정
    install_requires=[                 # 의존성 패키지
        "beautifulsoup4",
        "dnspython",
        "fastapi",
        "joblib",
        "pandas",
        "pydantic",
        "pymongo",
        "python_whois",
        "Requests",
        "selenium",
        "tldextract",
        "webdriver_manager",
        "xgboost"
    ],
    entry_points={
        "console_scripts": [
            "phpyphishing=pyback.main:run_server"  # main.py의 app을 실행
        ]
    },
    description="Phishing detection using FastAPI and XGBoost",
    author="Your Name",
    author_email="your_email@example.com",
    url="https://github.com/parkwookyong/PHPHPH",
    python_requires=">=3.8",
)
