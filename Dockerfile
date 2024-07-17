FROM python:3.10.14-bookworm

WORKDIR /app

RUN apt-get update && apt-get install usbutils -y && pip install --upgrade pip 

COPY . /app/dali2mqtt

RUN cd dali2mqtt && pip install -r requirements.txt

WORKDIR /app/dali2mqtt

ENTRYPOINT ["python", "-m", "dali2mqtt.dali2mqtt", "--config", "/app/dali-config/config.yaml"]
