from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

# 테스트 방법
# uvicorn api_read:app --reload
# 테스트 방법(외부)
# 192.168.0.66:8000
# 192.168.0.66:8000/docs
# uvicorn api_read:app --host 0.0.0.0 --port 8000 --reload

# get : 조회 / 파라미터가 url에 유출됨(body에 못 담음)
# post : 업데이트, 생성 / 파라미터가 url에 유출이 안됨(body에 담아서 보내니까)

app = FastAPI()

# COSRS옵션 부여
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 연결 설정(읽기속도 특화)
connection_string = "mongodb://192.168.56.100:32018/?replicaSet=rs0&directConnection=true"
client = MongoClient(connection_string)
db = client["im"]
collection = db["InterviewMaster"]



# 전체 데이터 조회(테스트용)
@app.get("/getdata")
async def get_data():
    # MongoDB에서 모든 문서 조회
    data = list(collection.find({}))
    return {"data": data}



# 로그인시 정보 제공(oauth확인 후 작성)


# 마이페이지(정보) 조회
# get
# 입력값 user_id
# 출력값 user_id, user_inf, user_history
@app.get("/getuser/{user_id}")
async def get_user(user_id: str):

    user = collection.find_one({"_id": user_id}, {"_id": 0, "user_info": 1, "user_history": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "user_info": user.get("user_info"),
        "user_history": user.get("user_history")
    }



# 마이페이지(면접, 질문) 조회
# get
# 입력값 user_id
# 출력값 user_id, user_history, itv_info
@app.get("/getitv/{user_id}")
async def get_itv(user_id: str):

    user = collection.find_one({"_id": user_id}, {"_id": 0, "user_history": 1})
    itv = collection.find_one({"_id": user_id}, {"_id": 0, "itv_info": 1})

    if not itv:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "user_history": user.get("user_history"),
        "itv_info": itv.get("itv_info")
    }