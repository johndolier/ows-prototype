FROM python:3.11-buster

RUN mkdir app
WORKDIR /app

ENV PATH="${PATH}:/root/.local/bin"
ENV PYTHONPATH=.

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN python3 -m spacy download en_core_web_sm

COPY src/ /app/src
COPY assets/ /app/assets

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
