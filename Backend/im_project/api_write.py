from fastapi import FastAPI, HTTPException, Request
from pymongo import MongoClient
from datetime import datetime
import re

# 테스트 방법
# uvicorn api_write:app --reload
# 테스트 방법(외부)
# 192.168.0.66:8001
# 192.168.0.66:8001/docs
# uvicorn api_write:app --host 0.0.0.0 --port 8001 --reload

# 생성 테스트 : cmd창에서 테스트
# curl -X POST "http://192.168.0.66:8001/create_user" -H "Content-Type: application/json" -d "{\"email\": \"T1@T1.com\", \"user_nm\": \"Faker\", \"user_nicknm\": \"불사대마왕\", \"user_gender\": \"남\", \"user_birthday\": \"1999-09-09\", \"user_tel\": \"010-9999-9999\"}"

# get : 조회 / 파라미터가 url에 유출됨(body에 못 담음)
# post : 업데이트, 생성 / 파라미터가 url에 유출이 안됨(body에 담아서 보내니까)

app = FastAPI()

# MongoDB 연결 설정(쓰기속도 특화)
connection_string = "mongodb://192.168.56.100:32017/?replicaSet=rs0&directConnection=true"
client = MongoClient(connection_string)
db = client["im"]
collection = db["InterviewMaster"]



# 회원가입((oauth확인 후 작성)



# 신규 사용자 생성(curl로 입력 받아서 생성 되는 기준으로 작성)  
# post
# 입력값 user_id, emial, 성명, 별명, 성별, 생년월일, 연락처
@app.post("/create_user")
async def create_user(request: Request):
    try:
        # 요청 데이터 가져오기
        data = await request.json()
        email = data.get("email")
        user_nm = data.get("user_nm")
        user_nicknm = data.get("user_nicknm")
        user_gender = data.get("user_gender")
        user_birthday = data.get("user_birthday")
        user_tel = data.get("user_tel")

        # 필수 필드 검증
        if not all([email, user_nm, user_nicknm, user_gender, user_birthday, user_tel]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # 이메일을 _id로 사용하여 새 사용자 데이터 생성
        new_user = {
            "_id": email,
            "user_info": {
                "user_nm": user_nm,
                "user_nicknm": user_nicknm,
                "user_gender": user_gender,
                "user_birthday": user_birthday,
                "user_tel": user_tel,
            },
            "user_history": {
                "user_itv_cnt": 0
            },
            "itv_info": {}
        }
        
        # MongoDB에 새 사용자 데이터 삽입
        result = collection.insert_one(new_user)
        
        if result.inserted_id:
            return {"message": "User created successfully", "user_id": result.inserted_id}
        else:
            raise HTTPException(status_code=400, detail="User creation failed")

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# 마이페이지 수정
# post
# 입력값 user_id, 성명, 별명, 성별, 생년월일, 연락처

# T1@T1.com
# Faker
# 불사대마왕
# 남
# 1999-09-09
# 010-9999-9999
@app.post("/mod_user")
async def mod_user(user_id: str, user_nm: str, user_nicknm: str, user_gender: str, user_birthday: str, user_tel: str):
    try:
        # user_id에 해당하는 값 가져오기
        user = collection.find_one({"_id": user_id})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        print("User data:", user)
        
        # 업데이트할 필드들
        update_fields = {}

        if user_nm != user.get("user_info", {}).get("user_nm"):
            update_fields["user_info.user_nm"] = user_nm    
        if user_nicknm != user.get("user_info", {}).get("user_nicknm"):
            update_fields["user_info.user_nicknm"] = user_nicknm
        if user_gender != user.get("user_info", {}).get("user_gender"):
            update_fields["user_info.user_gender"] = user_gender
        if user_birthday != user.get("user_info", {}).get("user_birthday"):
            update_fields["user_info.user_birthday"] = user_birthday
        if user_tel != user.get("user_info", {}).get("user_tel"):
            update_fields["user_info.user_tel"] = user_tel

        # 업데이트할 필드가 있는 경우에만 업데이트 수행
        if update_fields:
            result = collection.update_one({"_id": user_id}, {"$set": update_fields})
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Update failed")

        return {"status": "success", "updated_fields": update_fields}

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# 모의면접 생성
# post
# 입력값 user_id, 자소서 url, 카테고리, 직무

# T1@T1.com
# http://url...
# 자소서
# 프로게이머
@app.post("/new_itv")
async def new_itv(user_id: str, itv_text_url: str, itv_cate: str, itv_job: str):
    try:
        # user_id에 해당하는 값 가져오기
        user = collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        print("User data:", user)
        
        # 면접번호생성을 위한 데이터 조회
        # 오늘 날짜 / email에서 .뒤부분 잘라내기 / user_history에서 면접번호 가져오기
        today_date6 = datetime.today().strftime('%y%m%d')
        today_date8 = datetime.today().strftime('%Y-%m-%d')
        user_id = user.get("_id",{})
        user_short_id = user.get("_id",{}).split('.')[0]
        user_history = user.get("user_history", {})
        user_itv_cnt = user_history.get("user_itv_cnt")
        print(f"Current user_id: {user_id}")
        print(f"Current user_itv_cnt: {user_itv_cnt}")
        
        # user_itv_cnt가 None이거나 0이거나 문자열로 된 경우 처리
        if user_itv_cnt is None or user_itv_cnt == 0:
            user_itv_cnt = 1
        else:
            # 문자열에서 정수 추출
            if isinstance(user_itv_cnt, str):
                match = re.search(r'\d+$', user_itv_cnt)
                if match:
                    user_itv_cnt = int(match.group())
                else:
                    user_itv_cnt = 0
            user_itv_cnt += 1
        print(f"New user_itv_cnt: {user_itv_cnt}")
        
        # 면접번호, 면접제목 생성!
        new_itv_key = f"{user_short_id}_{today_date6}_{str(user_itv_cnt).zfill(3)}"
        new_itv_sub = f"{user.get("user_info", {}).get("user_nicknm")}_{itv_cate}_모의면접_{str(user_itv_cnt).zfill(3)}"
        print(f"New itv_info key: {new_itv_key}")
        print(f"New itv_info sub: {new_itv_sub}")

        # 면접 데이터 생성
        new_itv_info = {
            new_itv_key: {
                "itv_sub": new_itv_sub,
                "itv_text_url": itv_text_url,
                "itv_cate": itv_cate,
                "itv_job": itv_job,
                "itv_qs_cnt": "0",
                "itv_date": today_date8,
                "qs_info": {}
            }
        }

        # update문 생성
        update_query = {
            "$set": {
                "user_history.user_itv_cnt": user_itv_cnt,
                f"itv_info.{new_itv_key}": new_itv_info[new_itv_key]
            }
        }
        print("Update query:", update_query)
        
        # update실행!
        result = collection.update_one({"_id": user_id}, update_query)

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Update failed")
        return {"message": "Update successful"}

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# 질문 종료시 질문정보/결과 저장(n번 수행)
# post
# 입력값 user_id, 모의면접번호, 질문번호, 질문내용, 비디오, 오디오, 텍스트 url정보

# T1@T1.com
# T1@T1_240614_001
# 01 ~ n번
# 자신의 강점에 대해서 설명해보세요.
# s3://simulation-userdata/video/1718263662009test.mp4
# s3://simulation-userdata/audio/1718324990967.mp3
# s3://simulation-userdata/text/test.txt
@app.post("/update_qs")
async def update_qs(user_id: str, itv_no: str, qs_no: str, qs_content: str, qs_video_url: str, qs_audio_url: str, qs_text_url: str):
    try:
        # user_id에 해당하는 값 가져오기
        user = collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        print("User data:", user)

        # 질문번호에 대한 데이터 업데이트
        new_qs_info = {
            "qs_content": qs_content,
            "qs_video_url": qs_video_url,
            "qs_audio_url": qs_audio_url,
            "qs_text_url": qs_text_url,
            "qs_fb_url": ""
        }

        # update문 생성
        update_query = {
            "$set": {
                f"itv_info.{itv_no}.qs_info.{qs_no}": new_qs_info
            }
        }
        print("Update query:", update_query)
        
        # update실행!
        result = collection.update_one({"_id": user_id}, update_query)
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Update failed")

        return {"status": "success", "updated_fields": new_qs_info}

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# 총 질문 개수 반영
# post
# 입력값 user_id, 모의면접번호, 질문개수

# T1@T1.com
# T1@T1_240614_001
# n개
@app.post("/update_itv_qs_cnt")
async def update_fb(user_id: str, itv_no: str, itv_qs_cnt: int):
    try:
        # user_id에 해당하는 값 가져오기
        user = collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        print("User data:", user)

        # update문 생성
        update_query = {"$set": {f"itv_info.{itv_no}.itv_qs_cnt": itv_qs_cnt}}
        print("Update query:", update_query)
        
        # update실행!
        result = collection.update_one({"_id": user_id}, update_query)
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Update failed")

        return {"status": "success", "updated_fields": update_query}

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# 면접 종료시 결과url 반영(n번 수행)
# post
# 입력값 user_id, 모의면접번호, 질문번호, 피드백 url정보

# T1@T1.com
# T1@T1_240614_001
# 01 ~ n번
# http://url...
@app.post("/update_fb")
async def update_fb(user_id: str, itv_no: str, qs_no: str, qs_fb_url: str):
    try:
        # user_id에 해당하는 값 가져오기
        user = collection.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        print("User data:", user)

        # update문 생성
        update_query = {"$set": {f"itv_info.{itv_no}.qs_info.{qs_no}.qs_fb_url": qs_fb_url}}
        print("Update query:", update_query)
        
        # update실행!
        result = collection.update_one({"_id": user_id}, update_query)
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Update failed")

        return {"status": "success", "updated_fields": update_query}

    except Exception as e:
        print("Exception occurred:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)