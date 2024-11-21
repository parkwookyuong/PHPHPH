from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from pyback.predict import PhishingDetectionModel
from pyback.utils import is_url_in_collection
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# MongoDB 연결 설정
client = MongoClient('mongodb://localhost:27017/')
db = client['qr_data_url']
whitelist_collection = db['whitelist_urls']
blacklist_collection = db['blacklist_urls']

# FastAPI 앱 초기화
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 초기화
model_path = 'C:/Users/dnrud/OneDrive/Desktop/CCIT2/Phishing_model_02.pkl'
phishing_model = PhishingDetectionModel(model_path)

# 요청 데이터 모델
class URLRequest(BaseModel):
    url: str

@app.post('/check-url')
async def check_url(request: URLRequest):
    is_whitelisted = is_url_in_collection(request.url, whitelist_collection)
    is_blacklisted = is_url_in_collection(request.url, blacklist_collection)

    if not is_whitelisted and not is_blacklisted:
        try:
            prediction = phishing_model.predict_url(request.url)
            if prediction == -1:
                raise HTTPException(status_code=400, detail="Prediction failed")
            return {
                "isWhitelisted": is_whitelisted,
                "isBlacklisted": is_blacklisted,
                "prediction": prediction,
                "message": "URL was not in database; ML verification performed."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during ML prediction: {str(e)}")

    return {
        "isWhitelisted": is_whitelisted,
        "isBlacklisted": is_blacklisted,
        "prediction": None,
        "message": "URL found in database; no ML verification needed."
    }
    
# 서버 실행 함수
def run_server():
    uvicorn.run("pyback.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run_server()
