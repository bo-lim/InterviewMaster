FROM python:3.10
COPY . /src
WORKDIR /src
RUN apt-get update -y && apt-get install -y xdg-utils
RUN pip install --upgrade pip && pip install -r requirement.txt && pip install torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
EXPOSE 8000
CMD ["uvicorn","speech:app", "--host", "0.0.0.0", "--port", "8000"]
