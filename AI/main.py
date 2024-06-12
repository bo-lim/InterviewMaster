from fastapi import FastAPI
import torch
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
from pydantic import BaseModel

tokenizer = PreTrainedTokenizerFast.from_pretrained('bo-lim/IM-text-model')
model = BartForConditionalGeneration.from_pretrained('bo-lim/IM-text-model')

app = FastAPI()

class Item(BaseModel):
    text: str

@app.post("/analyze/summarize")
async def summarize(item: Item):
    text = item.text.replace('\n', ' ')
    raw_input_ids = tokenizer.encode(text)
    input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]

    # 요약 생성
    summary_ids = model.generate(torch.tensor([input_ids]), num_beams=4, max_length=512, eos_token_id=1)
    summary = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
    return {"result":summary}