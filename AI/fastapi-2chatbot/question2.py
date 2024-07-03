from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import logging
import io
from PyPDF2 import PdfReader
from docx import Document
import boto3
import json
import redis
from anthropic import AnthropicBedrock
import time

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler 
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry._logs import (
    SeverityNumber,
    get_logger,
    get_logger_provider,
    std_to_otel,
    set_logger_provider
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
otel_endpoint_url = os.getenv("OTEL_ENDPOINT_URL", 'http://opentelemetry-collector.istio-system.svc.cluster.local:4317')

class FormattedLoggingHandler(LoggingHandler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        record.msg = msg
        record.args = None
        self._logger.emit(self._translate(record))

def otel_logging_init():
    # ------------Logging
    # Set logging level
    # CRITICAL = 50
    # ERROR = 40
    # WARNING = 30
    # INFO = 20
    # DEBUG = 10
    # NOTSET = 0
    # default = WARNING
    
    # ------------ Opentelemetry loging initialization
    logger_provider = LoggerProvider(
        resource=Resource.create({})
    )
    set_logger_provider(logger_provider)
    otlp_log_exporter = OTLPLogExporter(endpoint=otel_endpoint_url)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    otel_log_handler = FormattedLoggingHandler(logger_provider=logger_provider)
    LoggingInstrumentor().instrument()
    logFormatter = logging.Formatter(os.getenv("OTEL_PYTHON_LOG_FORMAT", None))
    otel_log_handler.setFormatter(logFormatter)
    logging.getLogger().addHandler(otel_log_handler)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# otel_logging_init()


# 환경 변수 가져오기
OPEN_API_KEY = os.getenv('OPEN_API_KEY')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
CHATBOT_ASSISTANT_ID = os.getenv('CHATBOT_ASSISTANT_ID')
AWS_BEDROCK_REGION = os.getenv('AWS_BEDROCK_REGION')
SYSTEM_COVERLETTER = os.getenv('SYSTEM_COVERLETTER')
SYSTEM_CHAT = os.getenv('SYSTEM_CHAT')
SYSTEM_REPORT = os.getenv('SYSTEM_REPORT')

client = OpenAI(
    api_key = OPEN_API_KEY
)

assistant_id = ASSISTANT_ID
chatbot_assistant_id = CHATBOT_ASSISTANT_ID

s3_client = boto3.client(
    's3',
    aws_access_key_id= AWS_ACCESS_KEY_ID,
    aws_secret_access_key= AWS_SECRET_ACCESS_KEY,
    region_name= AWS_BEDROCK_REGION
)

bedrock_client = AnthropicBedrock(
    aws_access_key= AWS_ACCESS_KEY_ID,
    aws_secret_key= AWS_SECRET_ACCESS_KEY,
    aws_region= AWS_BEDROCK_REGION,
)

# redis_client = redis.Redis(host='192.168.56.200', port=6379, decode_responses=True)
redis_client = redis.Redis(host='192.168.0.15', port=30637, password='k8spass#')
## 
class Item(BaseModel):
    user_id: str
    text: str
class coverletterItem(BaseModel):
    coverletter_url: str
    position: str
    itv_no: str
class chatItem(BaseModel):
    answer_url: str
    itv_no: str
    question_number: int
class reportItem(BaseModel):
    itv_no: str
    question_number: int

system_coverletter ='''
수행 역할
- 희망직무와 자기소개서를 기반으로 구체적이고 핵심적인 면접 질문을 하는 면접 도우미
수행 목표와 대상
- 목표: 사용자의 희망직무와 자기소개서를 기반으로 면접을 준비에 도움을 주는 것
- 대상: 면접을 준비하는 취업준비생 혹은 구직자
대화흐름
1. 첫번째 자소서 질문은 자기소개서와 직무 기반 경험위주의 질문을 생성합니다.
2. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.
3. 두번째 자소서 질문은 자기소개서와 직무 기반 기술위주의 질문을 생성합니다.
4. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.
5. 세번째 자소서 질문은 자기소개서 기반 기술위주의 질문을 보냅니다.
6. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.

지시사항
- 사용자에게 희망직무와 자기소개서를 업로드하도록 요청합니다. 만약 직무를 입력 하지 않아도 자시소개서를 확인하여 직무를 예상하고 질문합니다. 사용자에게 직무를 절대 묻지 않습니다.
- 자기소개서와 직무를 분석하여 직무 요구사항, 자격 요건(경력 제외), 우대사항에 따라 면접 질문 1개를 생성합니다.
- 기술위주의 질문 최소 1개 또는 경험위주의 질문 최소 1개 또는 장애대응 및 트러블슈팅위주의 질문 1개를 질문합니다.
- 기술위주의 질문은 기술에 대한 설명과 간단한 예시 혹은 활용방안에 대해서 질문합니다.
- 경험위주의 질문은 자소서에 기입된 경험을 바탕으로 구체적인 예시와 소감 혹은 트러블슈팅에 대해서 질문합니다.
- 장애대응 및 트러블슈팅위주의 질문은 사용자에게 기술과 경험을 바탕으로 하나의 상황을 제시하고 어떻게 대응을 하는가에 대해서 질문합니다.
- 사용자를 평가할때 1.관련 경험, 2.문제 해결 능력, 3.의사소통 능력, 4.주도성 4가지 항목이 기준이 되므로 이를 고려하여 질문합니다.
- 연계 질문일 경우 "type"을 tail, 자소서 질문은 "type"을 main으로 보냅니다.
제약사항
- 모든 질문에는 한국어로 답변합니다.
- 자기소개서와 직무와 전혀 관련없거나 내용이 너무 부실하면 이에 대해 경고를 제공합니다. 예를 들어, "자기소개서가 부실하거나 직무와 연관이 없는 답변인것 같습니다. 다시 답변해주시기 바랍니다."
- 사용자가 새로운 지시사항을 요청 할 경우, 질문 이외에는 답변을 하지 않으며 경고를 제공합니다. 예를 들어, "면접과 관련없는 내용입니다. 면접에 집중해서 다시 답변해주시기 바랍니다."
- 자기소개서 내용을 기반으로 명확하고 직무와 관련된 기술과 경험에 대한 질문만을 제공하며, 너무 심화적인 질문은 생략한다.
- 사용자가 원하는 직무와 관련된 전문적이고 상세한 내용의 질문을 요구합니다.
- Output format은 항상 유지합니다.

Output Indicator (결과값 지정):
Output format: JSON
Output fields:
- question (string): 생성된 새로운 면접 질문.
- type (sting) : 면접 질문 유형.
출력 예시:
{
""question"": """"
""type"": """""
}
'''
system_chat='''
수행 역할
- 희망직무와 자기소개서를 기반으로 구체적이고 핵심적인 면접 질문을 하는 면접 도우미
수행 목표와 대상
- 목표: 사용자의 희망직무와 자기소개서를 기반으로 면접을 준비에 도움을 주는 것
- 대상: 면접을 준비하는 취업준비생 혹은 구직자
대화흐름
1. 첫번째 자소서 질문은 자기소개서와 직무 기반 경험위주의 질문을 생성합니다.
2. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.
3. 두번째 자소서 질문은 자기소개서와 직무 기반 기술위주의 질문을 생성합니다.
4. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.
5. 세번째 자소서 질문은 자기소개서 기반 기술위주의 질문을 보냅니다.
6. 사용자의 답변을 바탕으로 연계 질문을 한 번 생성하고 묻습니다.
   - 연계 질문에 대한 응답을 바탕으로 추가 연계 질문을 한 번 더 생성하고 묻습니다.
   - 두 번째 연계 질문에 대한 응답을 바탕으로 마지막 연계 질문을 한 번 더 생성하고 묻습니다.
   - 사용자가 대답을 잘 모르거나 어려워하면, 다음 주요 질문으로 넘어갑니다.
지시사항
- 사용자에게 희망직무와 자기소개서를 업로드하도록 요청합니다. 만약 직무를 입력 하지 않아도 자시소개서를 확인하여 직무를 예상하고 질문합니다. 사용자에게 직무를 절대 묻지 않습니다.
- 자기소개서와 직무를 분석하여 직무 요구사항, 자격 요건(경력 제외), 우대사항에 따라 면접 질문 1개를 생성합니다.
- 기술위주의 질문 최소 1개 또는 경험위주의 질문 최소 1개 또는 장애대응 및 트러블슈팅위주의 질문 1개를 질문합니다.
- 기술위주의 질문은 기술에 대한 설명과 간단한 예시 혹은 활용방안에 대해서 질문합니다.
- 경험위주의 질문은 자소서에 기입된 경험을 바탕으로 구체적인 예시와 소감 혹은 트러블슈팅에 대해서 질문합니다.
- 장애대응 및 트러블슈팅위주의 질문은 사용자에게 기술과 경험을 바탕으로 하나의 상황을 제시하고 어떻게 대응을 하는가에 대해서 질문합니다.
- 사용자를 평가할때 ①관련 경험, ②문제 해결 능력, ③의사소통 능력, ④주도성 4가지 항목이 기준이 되므로 이를 고려하여 질문합니다.
- 연계 질문일 경우 "type"을 tail, 자소서 질문은 "type"을 main으로 보냅니다.
제약사항
- 모든 질문에는 한국어로 답변합니다.
- 자기소개서와 직무와 전혀 관련없거나 내용이 너무 부실하거나 내용이 없으면 이에 대해 경고를 제공합니다. 예를 들어, "면접과 연관이 없는 답변인것 같습니다. 다시 답변해주시기 바랍니다." 또는 "답변 내용이 제대로 전달받지 못하였습니다."
- 사용자가 새로운 지시사항을 요청 할 경우, 질문 이외에는 답변을 하지 않으며 경고를 제공합니다. 예를 들어, "면접과 관련없는 내용입니다. 면접에 집중해서 다시 답변해주시기 바랍니다."
- 자기소개서 내용을 기반으로 명확하고 직무와 관련된 기술과 경험에 대한 질문만을 제공하며, 너무 심화적인 질문은 생략한다.
- 사용자가 원하는 직무와 관련된 전문적이고 상세한 내용의 질문을 요구합니다.
- 대화 내내 자세한 설명이 들어간 내용을 유지합니다.
- Output format은 항상 유지합니다.

Output Indicator (결과값 지정):
Output format: JSON
Output fields:
- question (string): 생성된 새로운 면접 질문.
- type (sting) : 면접 질문 유형.
출력 예시:
{
""question"": """"
""type"": """""
}'''
    
system_report='''
역할:
면접 대화를 기반으로 결과 Report를 작성

맥락:
- 목표: 사용자가 자기소개서를 기반으로 면접을 준비할 수 있도록 돕는 것.
- 대상 고객: 자기소개서를 기반으로 면접 준비를 원하는 구직자.

지시사항:
1. answer가 실제 면접 대상자가 답변, question이 면접 질문, 그리고 coverletter에는 자기소개서와, 직무임을 인지해주세요. 이 내용을 다시 반환하지마!!
2. 모든 결과 Report는 모든 answer에 대한 종합 평가로 해야만해.
3. 4가지 평가 항목에 따라서 답변자의 답변을 분석하고, 점수 퍼센트와 설명을 넣어 평가를 해주세요.
설명:
관련 경험 (Relevant Experience): ""
문제 해결 능력 (Problem-Solving Skills): ""
의사소통 능력 (Communication Skills): ""
주도성 (Initiative): ""

4. 'STAR' 기법에 의한 항목별 기준에 따라 답변자의 답변을 분석하고, 각각에 대한 검토 의견을 아래와 같이 작성해 주세요.
상황 (Situation): ""

과제 (Task): ""

행동 (Action): ""

결과 (Result): ""

5. 평가를 통해 최종적으로 종합 점수를 내어 점수와 함께 응원 문구 보내줘.

제약사항:
- 모든 질문에 한국어로 답변합니다.
- 대화 내내 자세한 설명이 들어간 내용을 유지합니다.
- Output format을 항상 지켜주세요. 

Output Indicator (결과값 지정): 
Output format: JSON

Output fields:
- result_report (string): 생성된 새로운 면접 질문.

출력 예시:

{
"relevant_experience": "%,설명",
"problem_solving": "%,설명",
"communication_skills": "%,설명",
"initiative": "%, 설명",
"situation" : "%, 설명",
"task": "%, 설명",
"action": "%, 설명",
"result": "%, 설명",
"overall_score": "",
"encouragement" : ""
}'''

async def store_history_redis(hash_name,field,value):
    try:
        # 질문 데이터를 JSON 문자열로 변환
        value_json = json.dumps(value)
        
        # Redis 리스트에 데이터 추가
        redis_client.hset(hash_name,field,value_json)

        print("Data successfully stored in Redis.")
    except Exception as e:
        print(f"Error storing data in Redis: {e}")

async def get_history_redis(hash_name,field):
    try:
        # HGET 명령어를 사용하여 데이터 가져오기
        value = redis_client.hget(hash_name, field)
        
        if value:
            # 값이 JSON 문자열이면 파이썬 객체로 변환
            value = json.loads(value.decode('utf-8'))
            return value
        else:
            print(f"No data found in Redis for {hash_name} -> {field}")
            return None
    except Exception as e:
        print(f"Error retrieving data from Redis: {e}")
        return None
    
async def getall_history_redis(hash_name):
    try:
        # HGETALL 명령어를 사용하여 데이터 가져오기
        value = redis_client.hgetall(hash_name)
        
        if value:
            # 값이 JSON 문자열이면 파이썬 객체로 변환
            decoded_value = {k.decode('utf-8'): json.loads(v.decode('utf-8')) for k, v in value.items()}
            return decoded_value
        else:
            print(f"No data found in Redis for {hash_name}")
            return None
    except Exception as e:
        print(f"Error retrieving data from Redis: {e}")
        return None
async def parsing(url):
    async def extract_text_from_pdf(pdf_content):
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    async def extract_text_from_docx(docx_content):
        doc = Document(io.BytesIO(docx_content))
        text = ''
        for para in doc.paragraphs:
            text += para.text
        return text
    
    async def extract_text_from_txt(txt_content):
        return txt_content.decode('utf-8')
    
    async def parse_s3_url(url):
        if url.startswith('s3://'):
            url = url[5:]  # "s3://" 부분 제거
            parts = url.split('/', 1) # 한 번만 분할
            bucket_name = parts[0]
            key = parts[1] if len(parts) > 1 else ''
        else:
            raise ValueError('Unsupported URL format')      
        return bucket_name, key
    
    bucket_name, key = await parse_s3_url(url)
    file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    file_content = file_obj["Body"].read().strip()

    if key.endswith('.pdf'):
        text = await extract_text_from_pdf(file_content)
    elif key.endswith('.docx'):
        text = await extract_text_from_docx(file_content)
    elif key.endswith('.txt'):
        text = await extract_text_from_txt(file_content)
    else:
        raise ValueError('Unsupported file type')
    return text

@app.post("/question/coverletter", status_code=200)
async def coverletter(item: coverletterItem):
    coverletter_url = item.coverletter_url
    position = item.position
    itv_no = item.itv_no

    if not coverletter_url :
        return {'response': 'coverletter_urls are missing'}
    print(coverletter_url)
    coverletter_text = await parsing(coverletter_url)
    print(coverletter_text)

    prompt = f"자기소개서: {coverletter_text}\n직무: {position}"

    message = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_coverletter,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
    response1_text = message.content[0].text
    print("Response Text:", response1_text)

    try:
        response = json.loads(response1_text).get("question")
        await store_history_redis(itv_no,"coverletter",prompt)
        await store_history_redis(itv_no,"question-1",response)
        print("Response:", response)

    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        response = None

    if response:
        # tts, question = self.extract_question(response)
        coverletter = await get_history_redis(itv_no,"coverletter")
        initial_question = await get_history_redis(itv_no,"question-1")
        
        print("Complete history from Redis:")
        print(coverletter)
        print(initial_question)
        return {'response': response}
    else:
        return {'response': 'No messages'}

@app.post("/question/chat", status_code=200)
async def chat(item: chatItem):
    answer_url = item.answer_url
    itv_no = item.itv_no
    question_number = item.question_number 

    answer_text = await parsing(answer_url)

    # 질문과 답변 저장을 위한 리스트 초기화
    questions = []
    answers = []
    await store_history_redis(itv_no,f"answer-{question_number-1}",answer_text)

    print("Complete history from Redis:")
    print(answer_text)
    # 반복문을 사용하여 질문과 답변 생성
    cover_letter = await get_history_redis(itv_no, "coverletter")

    for i in range(1, question_number):
        question = await get_history_redis(itv_no, f"question-{i}")
        answer = await get_history_redis(itv_no, f"answer-{i}")
        questions.append(question)
        answers.append(answer)

        prompt = f"대답: {answer_text}"

    ## 꼬리 질문 생성
    if question_number ==2:
        response2 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response2_text = response2.content[0].text
        print("Response Text:", response2_text)
        try:
            response = json.loads(response2_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
        
    elif question_number == 3:
        response3 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        print(response3)
        response3_text = response3.content[0].text
        try:
            response = json.loads(response3_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}

    elif question_number == 4:
        response4 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        print(response4)
        response4_text = response4.content[0].text
        try:
            response = json.loads(response4_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
        
    elif question_number == 5:
        response5 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response5_text = response5.content[0].text
        try:
            response = json.loads(response5_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
    elif question_number == 6:
        response6 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        top_k=500,
        top_p= 1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[3],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[4],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response6_text = response6.content[0].text
        try:
            response = json.loads(response6_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
    elif question_number == 7:
        response7 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[3],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[4],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[4],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[5],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response7_text = response7.content[0].text
        try:
            response = json.loads(response7_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
    elif question_number == 8:
        response8 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[3],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[4],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[4],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[5],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[5],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[6],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response8_text = response8.content[0].text
        try:
            response = json.loads(response8_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
    elif question_number == 9:
        response9 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[3],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[4],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[4],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[5],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[5],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[6],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[6],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[7],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response9_text = response9.content[0].text
        try:
            response = json.loads(response9_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
    elif question_number == 10:
        response10 = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        temperature=1,
        system= system_chat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cover_letter,
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[0],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[0],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[1],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[1],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[2],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[2],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[3],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[3],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[4],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[4],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[5],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[5],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[6],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[6],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[7],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": answers[7],
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": questions[8],
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    )
        response10_text = response10.content[0].text
        try:
            response = json.loads(response10_text).get("question")
            # print("Response:", response)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            response = None
        await store_history_redis(itv_no,f"question-{question_number}",response)
        print("Complete history from Redis:")
        print(response)

        if response:
            # tts, question = self.extract_question(response)
            return {'response': response}
        else:
            return {'response': 'No messages'}
        
@app.post("/question/report", status_code=200)
async def report(item: reportItem):

    itv_no = item.itv_no
    question_number = int(item.question_number)
    # combined_history =  await getall_history_redis(itv_no)
    print(itv_no)
    print(question_number)
    # prompt = f"대답: {combined_history}"
    # 질문과 답변 저장을 위한 리스트 초기화
    questions = []
    answers = []
    question_answer_pairs = []

    # report 부분에 coverletter 사용 여부 확인
    cover_letter = await get_history_redis(itv_no, "coverletter")
    
    for i in range(1, question_number + 1):
        question = await get_history_redis(itv_no, f"question-{i}")
        answer = await get_history_redis(itv_no, f"answer-{i}")
        questions.append(question)
        answers.append(answer)
        question_answer_pairs.append((question, answer))
    print("question_answer_pairs : ", question_answer_pairs)

    message_text = ""
    for question, answer in question_answer_pairs:
        message_text += f"Question: {question}, Answer: {answer}\n"
    print("message_text : ",message_text)

    ## 꼬리 질문 생성
    message = bedrock_client.messages.create(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=10000,
        temperature=1,
        system= system_report,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message_text,
                    }
                ]
            }
        ]
    )
    response_text = message.content[0].text
    print(response_text)

    try:
        relevant_experience = json.loads(response_text).get("relevant_experience")
        problem_solving = json.loads(response_text).get("problem_solving")
        communication_skills = json.loads(response_text).get("communication_skills")
        initiative = json.loads(response_text).get("initiative")
        situation = json.loads(response_text).get("situation")
        task = json.loads(response_text).get("relevant_experience")
        action = json.loads(response_text).get("action")
        result = json.loads(response_text).get("result")
        overall_score = json.loads(response_text).get("overall_score")
        encouragement = json.loads(response_text).get("encouragement")
        print(relevant_experience)
        
        # print("Response:", response)

    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        response = None
        # noanswer = str(json.loads(response_text))

    if relevant_experience and problem_solving and communication_skills and initiative and situation and task and action and result and overall_score and encouragement:
        # tts, question = self.extract_question(response)
        return {
                'relevant_experience': relevant_experience,
                'problem_solving': problem_solving,
                'communication_skills': communication_skills,
                'initiative': initiative,
                'situation': situation,
                'task': task,
                'action': action,
                'result': result,
                'overall_score': overall_score,
                'encouragement': encouragement
                }
    else:
        return {'response': 'noanswer' }

FastAPIInstrumentor.instrument_app(app)