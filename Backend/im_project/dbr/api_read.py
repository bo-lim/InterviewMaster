from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from typing import Optional
from pymongo import MongoClient
from pydantic import BaseModel
import os, uuid, requests

# 테스트 방법(외부)
# 192.168.0.66:8000/docs
# uvicorn api_read:app --host 0.0.0.0 --port 8000 --reload

# get : 조회 / 파라미터가 url에 유출됨(body에 못 담음)
# post : 업데이트, 생성 / 파라미터가 url에 유출이 안됨(body에 담아서 보내니까)

app = FastAPI()


# .env파일 읽기
load_dotenv()

# COSRS옵션 부여
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 연결 설정(읽기속도 특화)
#connection_string = "mongodb://192.168.56.100:32018/?replicaSet=rs0&directConnection=true"
connection_string = os.getenv("DB_READ_LOC_URI")
client = MongoClient(connection_string)
db = client["im"]
collection = db["InterviewMaster"]


##########################
########## test ##########
##########################
# 전체 데이터 조회(테스트용)
@app.get("/dbr/get_data")
async def get_data():
    # MongoDB에서 모든 문서 조회
    data = list(collection.find({}))
    return {"data": data}



# UUID값 조회(테스트용)
@app.get("/dbr/get_uuid")
async def get_uuid():
    unique_id = uuid.uuid4()
    print("UUID 기본값 : ", unique_id, "\nUUID hex값 : ", unique_id.hex)
    return {
        "UUID 기본값": unique_id,
        "UUID hex값": unique_id.hex
    }

###########################
########## OAuth ##########
###########################
# kakao Login
# http://192.168.0.66:8002/act/kakao
# 호출시 auth로 redirect해서 인증 진행
@app.get("/dbr/act/kakao")
def kakao():
    kakao_client_key = os.getenv("KAKAO_CLIENT_KEY")
    kakao_url = os.getenv("KAKAO_REDIRECT_K8S_URI")
    kakao_scope = os.getenv("KAKAO_SCOPE")
    
    url = f"https://kauth.kakao.com/oauth/authorize?client_id={kakao_client_key}&redirect_uri={kakao_url}&response_type=code&scope={kakao_scope}"
    
    response = RedirectResponse(url)
    return response



# kakao 인증
# {
#   "code": {
#     "access_token": "access_token값",
#     "token_type": "bearer",
#     "refresh_token": "refresh_token값",
#     "id_token": "id_token값",
#     "expires_in": 21599,
#     "scope": "account_email openid profile_nickname",
#     "refresh_token_expires_in": 5183999
#   }
# }
@app.get("/dbr/act/kakao/auth")
async def kakaoAuth(response: Response, code: Optional[str]="NONE"):
    kakao_client_key = os.getenv("KAKAO_CLIENT_KEY")
    kakao_secret_key = os.getenv("KAKAO_SECRET_KEY")
    kakao_url = os.getenv("KAKAO_REDIRECT_K8S_URI")
    
    url = f'https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={kakao_client_key}&redirect_uri={kakao_url}&code={code}&client_secret={kakao_secret_key}'
    
    res = requests.post(url)
    result = res.json()

    print("*****/act/kakao/auth result*****\n", result, "\n********************************")
    access_token = result["access_token"]
    response.set_cookie(key="kakao", value=access_token)
    
    user_info_url = 'https://kapi.kakao.com/v2/user/me'
    # access_token을 이용해서 사용자 정보 받아오기
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_info_res = requests.get(user_info_url, headers=headers)
    user_info_result = user_info_res.json()
    print("*****user info result*****\n", user_info_result, "\n**************************")

    if 'kakao_account' in user_info_result and 'email' in user_info_result['kakao_account']:
        email = user_info_result['kakao_account']['email']

        # DB user체크 부분
        user = collection.find_one({"_id": email}, {"_id": 1, "user_info": 1, "user_history": 1})

        # user정보가 없을 경우에는 false값 넘겨줘서 신규가입 화면으로
        # user정보가 있을 경우에는 true값 넘겨줘서 마이페이지 확인 화면 or 메인페이지로
        if not user:
            print("*****user info DB result*****\n신규유저 : ", user, "\n*****************************")
            url = f"http://192.168.0.34:3000/auth?email_id={email}&access_token={access_token}&message=new"
        else:
            print("*****user info DB result*****\n기존유저 : ", user, "\n*****************************")
            url = f"http://192.168.0.34:3000/auth?email_id={email}&access_token={access_token}&message=main"

        response = RedirectResponse(url)
        return response
    else:
        return {"error": "Email not available"}



# kakao 로그아웃
# http://192.168.0.66:8002/act/kakao/logout
# access_token받아야 로그아웃 처리 가능
class ItemToken(BaseModel):
    access_token: str

@app.post("/dbr/act/kakao/logout")
def kakaoLogout(item: ItemToken, response: Response):
    try:
        access_token = item.access_token

        url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post(url, headers=headers)
        result = res.json()
        
        print("*****Logout result*****\n", result, "\n*****************************")
        
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to logout from Kakao")
        
        response.delete_cookie(key="kakao")
        return {"logout": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# kakao 로그아웃(강제)
# http://192.168.0.66:8002/act/kakao/kill
# access_token받아야 로그아웃 처리 가능
@app.get("/dbr/act/kakao/kill/{token}")
def kakaokill(token: str, response: Response):
    try:
        # 액세스 토큰(강제 kill)
        access_token = token

        url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post(url, headers=headers)
        result = res.json()
        
        print("*****Logout result*****\n", result, "\n*****************************")
        
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail="Failed to logout from Kakao")
        
        response.delete_cookie(key="kakao")
        return {"logout": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



###########################
########### DBR ###########
###########################
# 마이페이지(정보) 조회
# get
# 입력값 user_id
# 출력값 user_id, user_inf, user_history
@app.get("/dbr/get_user/{user_id}")
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
@app.get("/dbr/get_itv/{user_id}")
async def get_itv(user_id: str):

    user = collection.find_one({"_id": user_id}, {"_id": 0, "user_history": 1})
    itv = collection.find_one({"_id": user_id}, {"_id": 0, "itv_info": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "user_history": user.get("user_history"),
        "itv_info": itv.get("itv_info")
    }



# 면접 조회
# get
# 입력값 user_id, itv_no
# 출력값 user_id, user_history, itv_info
@app.get("/dbr/get_itv/{user_id}/{itv_no}")
async def get_itv_detail(user_id: str, itv_no: str):

    itv = collection.find_one({"_id": user_id}, {"_id": 0, f"itv_info.{itv_no}": 1})
    print("tt", itv)

    if not itv:
        raise HTTPException(status_code=404, detail="Itv not found")

    # 내가 원하는 특정 데이터만 가져와서 사용
    itv_info = itv.get("itv_info", {}).get(itv_no)

    return {
        "user_id": user_id,
        "itv_info": {itv_no: itv_info}
    }
