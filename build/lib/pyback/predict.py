import xgboost as xgb
import joblib
import pandas as pd
from pyback.crawler import Crawler


class PhishingDetectionModel:
    def __init__(self, model_path=None):
        # 모델 경로가 주어지면 해당 모델을 로드하고, 아니면 None으로 초기화
        if model_path:
            self.model = joblib.load(model_path)
        else:
            self.model = None
        self.crawler = Crawler()  # Crawler 클래스 인스턴스화

    def preprocess_data(self, df):
        # 불필요한 열 제거
        columns_to_drop = [
            'URL', 'IP Address', 'Country', 'User Country', 'Countries Match',
            'Creation Date', 'Expiration Date', 'Registrant Name', 'Final URL',
            'redirection_count', 'external_domain_requests', 'malicious_file_downloads'
        ]
        df = df.drop(columns=columns_to_drop, errors='ignore')

        # 불리언 값을 1과 0으로 변환
        bool_columns = [
            'Is Obfuscated', 'Window Location Redirect', 'SSL Used', 
            'Cookie Access', 'iframe_present', 'favicon', 'x frame option', 'spf', 'txt', 'lang'
        ]
        df[bool_columns] = df[bool_columns].astype(int)

        # 특정 열의 NaN 처리
        nan_columns = ['Hidden Iframe Count', 'Content Size (bytes)', 'Domain Age (days)']
        df[nan_columns] = df[nan_columns].apply(pd.to_numeric, errors='coerce')

        return df

    def predict_url(self, url):
        try:
            # 크롤링 데이터 수집
            result = self.crawler.crawl_website(url)
            if result is None:
                return -1  # 크롤링 실패 시

            # 크롤링 결과를 데이터프레임으로 변환
            df = pd.DataFrame([result])

            # 데이터 전처리
            processed_data = self.preprocess_data(df)

            # XGBoost DMatrix 형식으로 변환
            dmatrix_data = xgb.DMatrix(processed_data)

            # 예측
            prediction = self.model.predict(dmatrix_data)
            return int(prediction[0])
        except Exception as e:
            print(f"Error during prediction: {e}")
            return -1
