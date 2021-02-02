# Local Build Instructions:
# 1. From the repository root run the following
# $ docker build -f ./build/prodigy/Dockerfile .

FROM gcr.io/production-deployment/base-web:latest

ENV PRODIGY_HOME=/home/prodigy
WORKDIR /home/prodigy

# Expects the Prodigy python wheel to exist at ./research/prodigy/*
COPY ./research/prodigy/* ./
RUN pip3 install ./prodigy*.whl

COPY build/prodigy/requirements.txt ./ 
RUN pip3 install -r ./requirements.txt



ENTRYPOINT [ "/bin/bash", "-c" ]
EXPOSE 8080