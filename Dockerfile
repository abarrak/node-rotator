FROM python:3.8 as base

RUN apt-get update && apt-get -y upgrade && apt-get -y install bash git gcc

FROM base as build
WORKDIR /
COPY . .
RUN pip install -r requirements.txt

FROM build as runtime
CMD ["python", "src/main.py", "--help"]
