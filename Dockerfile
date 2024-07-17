FROM python:3.10.14-bookworm

WORKDIR /app

RUN /bin/sh -c apt-get update && apt-get install usbutils -y && pip install --upgrade pip 
RUN git clone https://github.com/binsentsu/dali2mqtt && cd dali2mqtt && pip install -r requirements.txt

WORKDIR /app/dali2mqtt

ENTRYPOINT ["python" "-m" "dali2mqtt.dali2mqtt" "--config" "/app/dali-config/config.yaml"]