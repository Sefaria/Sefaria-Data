# Local Build Instructions:
# 1. From the repository root run the following
# $ docker build -f ./build/prodigy/Dockerfile .

FROM gcr.io/production-deployment/base-web:latest

ENV PRODIGY_HOME=/home/prodigy
WORKDIR /home/prodigy

COPY ./research/prodigy/* ./
RUN pip3 install ./prodigy*.whl

ENTRYPOINT [ "/bin/bash", "-c" ]
EXPOSE 8080