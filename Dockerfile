FROM python:3.7

WORKDIR /home

COPY ./requirements.txt ./requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ./*.py ./app/

ENTRYPOINT ["python", "./app/main.py"]

CMD ["-nhr", "45000"]
