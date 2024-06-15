FROM python:3.10-alpine
COPY . /src
WORKDIR /src
RUN pip install -r requirement.txt
EXPOSE 8000
CMD ["uvicorn","speech:app", "--host", "0.0.0.0", "--port", "8000"]