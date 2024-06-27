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
import logging
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler 
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, SimpleLogRecordProcessor, ConsoleLogExporter
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
otel_endpoint_url = 'http://opentelemetry-collector.istio-system.svc.cluster.local:4317'
# resource = Resource(attributes={
#     SERVICE_NAME: "itm-bce-txt"
# })
# traceProvider = TracerProvider(resource=Resource.create({}))
# trace.set_tracer_provider(traceProvider)
# otlp_span_exporter = OTLPSpanExporter(endpoint="http://opentelemetry-collector.istio-system.svc.cluster.local:4317/v1/traces")
# trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_span_exporter))


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
    log_level = logging.INFO
    print(f"Using log level: NOTSET / {log_level}")

    # ------------ Opentelemetry loging initialization

    logger_provider = LoggerProvider(
        resource=Resource.create({})
    )
    set_logger_provider(logger_provider)
    otlp_log_exporter = OTLPLogExporter(endpoint=otel_endpoint_url)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    otel_log_handler = FormattedLoggingHandler(logger_provider=logger_provider)

    # This has to be called first before logger.getLogger().addHandler() so that it can call logging.basicConfig first to set the logging format
    # based on the environment variable OTEL_PYTHON_LOG_FORMAT
    LoggingInstrumentor().instrument()
    logFormatter = logging.Formatter(os.getenv("OTEL_PYTHON_LOG_FORMAT", None))
    otel_log_handler.setFormatter(logFormatter)
    logging.getLogger().addHandler(otel_log_handler)

def otel_trace_init():
    trace.set_tracer_provider(
       TracerProvider(
           resource=Resource.create({}),
       ),
    )
    otlp_span_exporter = OTLPSpanExporter(endpoint=otel_endpoint_url)
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_span_exporter))

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
DEBUG_LOG_OTEL_TO_CONSOLE = os.getenv("DEBUG_LOG_OTEL_TO_CONSOLE", 'False').lower() == 'true'
DEBUG_LOG_OTEL_TO_PROVIDER = os.getenv("DEBUG_LOG_OTEL_TO_PROVIDER", 'False').lower() == 'true'
otel_trace_init()
otel_logging_init()

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
    current_span = trace.get_current_span()
    if (current_span is not None) and (current_span.is_recording()):
        current_span.set_attributes(
            {
                "http.status_text": item.file_path,
                "otel.status_description": f"{item.itv_no} / {item.question_no}",
                "otel.status_code": "ERROR"
            }
        )
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
    logger.info(f'stt file path : {original_file_name}')
    # with tracer.start_as_current_span("foo"):
    #     print("Hello world!")
    
    s3.put_object(
        Body = transcript,
        Bucket = bucket,
        Key = original_file_name
    )
    return {"s3_file_path":'s3://'+bucket+'/'+original_file_name}
FastAPIInstrumentor.instrument_app(app)
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