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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 어느곳에서 접근을 허용할 것이냐
    allow_credentials=True,
    allow_methods=["*"], # 어떤 메서드에 대해서 허용할 것이냐("GET", "POST")
    allow_headers=["*"],
)
bucket = 'simulation-userdata'
session = Session(profile_name="bolimuser")
polly = session.client("polly")
s3 = session.client("s3")

tokenizer = PreTrainedTokenizerFast.from_pretrained('bo-lim/IM-text-model')
model = BartForConditionalGeneration.from_pretrained('bo-lim/IM-text-model')

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class Item(BaseModel):
    user_id: str
    text: str
class SttItem(BaseModel):
    user_id: str
    file_path: str
class TextItem(BaseModel):
    text: str

@app.post("/analyze/summarize")
async def summarize(item: TextItem):
    text = item.text.replace('\n', ' ')
    raw_input_ids = tokenizer.encode(text)
    input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]

    # 요약 생성
    summary_ids = model.generate(torch.tensor([input_ids]), num_beams=4, max_length=512, eos_token_id=1)
    summary = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
    return {"result":summary}

@app.post("/speech/stt", status_code=200)
async def stt(item: SttItem):
    print(item.file_path)
    # file_path = item.file_path.split(bucket)[1][1:]
    file_path = item.file_path
    local_file_path = item.user_id+".mp3"
    s3.download_file( 
        bucket,
        file_path,
        local_file_path
    )
    
    audio_file = open(local_file_path,"rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
    )
    now = datetime.now()
    original_file_name = 'text/' + str(now.timestamp()).replace('.','') + '_' + item.user_id + '.txt'
    print(original_file_name, transcript)
    
    s3.put_object(
        Body = transcript,
        Bucket = bucket,
        Key = original_file_name
    )
    return {"s3_file_path":'s3://'+bucket+'/'+original_file_name}

@app.post("/speech/tts", status_code=201)
async def tts(item: Item):
    text = item.text
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3",
                                            VoiceId="Seoyeon")
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            output = os.path.join(gettempdir(), item.user_id+".mp3")
            try:
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                print(error)
                sys.exit(-1)
    else:
        print("Could not stream audio")
        sys.exit(-1)

    # Play the audio using the platform's default player
    if sys.platform == "win32":
        os.startfile(output)
    else:
        # The following works on macOS and Linux. (Darwin = mac, xdg-open = linux).
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, output])
    
    return {'output':output}