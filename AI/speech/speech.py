from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import torch
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
bucket = 'simulation-userdata'
session = Session(
    aws_access_key_id=os.environ["aws_access_key_id"],
    aws_secret_access_key=os.environ["aws_secret_access_key"],
    region_name="ap-northeast-2")
polly = session.client("polly")
s3 = session.client("s3")

tokenizer = PreTrainedTokenizerFast.from_pretrained('bo-lim/IM-text-model')
model = BartForConditionalGeneration.from_pretrained('bo-lim/IM-text-model')

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class Item(BaseModel):
    user_id: str
    text: str
class SttItem(BaseModel):
    itv_no: str
    file_path: str
    question_no: int
class TextItem(BaseModel):
    text: str

# @app.post("/analyze/summarize")
# async def summarize(item: TextItem):
#     text = item.text.replace('\n', ' ')
#     raw_input_ids = tokenizer.encode(text)
#     input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]

#     # 요약 생성
#     summary_ids = model.generate(torch.tensor([input_ids]), num_beams=4, max_length=512, eos_token_id=1)
#     summary = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
#     return {"result":summary}

@app.post("/speech/stt", status_code=200)
async def stt(item: SttItem):
    print(item.file_path)
    print(item.itv_no)
    print(item.question_no)
    file_path = item.file_path
    local_file_path = item.itv_no+".mp3"
    s3.download_file( 
        bucket,
        file_path,
        local_file_path
    )
    
    with open(local_file_path,"rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
        )
    os.remove(local_file_path)
    original_file_name = 'text/' + item.itv_no + '_' + str(item.question_no) + '.txt'
    print(original_file_name, transcript)
    with tracer.start_as_current_span("text_file") as dataspan:
        dataspan.set_attribute("text_file.value", original_file_name)
    
    s3.put_object(
        Body = transcript,
        Bucket = bucket,
        Key = original_file_name
    )
    return {"s3_file_path":'s3://'+bucket+'/'+original_file_name}

# @app.post("/speech/tts", status_code=201)
# async def tts(item: Item):
#     text = item.text
#     try:
#         # Request speech synthesis
#         response = polly.synthesize_speech(Text=text, OutputFormat="mp3",
#                                             VoiceId="Seoyeon")
#     except (BotoCoreError, ClientError) as error:
#         # The service returned an error, exit gracefully
#         print(error)
#         sys.exit(-1)

#     if "AudioStream" in response:
#         with closing(response["AudioStream"]) as stream:
#             output = os.path.join(gettempdir(), item.user_id+".mp3")
#             try:
#                 with open(output, "wb") as file:
#                     file.write(stream.read())
#             except IOError as error:
#                 print(error)
#                 sys.exit(-1)
#     else:
#         print("Could not stream audio")
#         sys.exit(-1)

#     # Play the audio using the platform's default player
#     if sys.platform == "win32":
#         os.startfile(output)
#     else:
#         # The following works on macOS and Linux. (Darwin = mac, xdg-open = linux).
#         opener = "open" if sys.platform == "darwin" else "xdg-open"
#         subprocess.call([opener, output])
    
#     return {'output':output}