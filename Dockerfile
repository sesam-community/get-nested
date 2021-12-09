FROM python:3.7

MAINTAINER Tarjei Skrede "tarjei.skrede@sesam.io"

COPY ./service /service
WORKDIR /service

RUN pip install -r requirements.txt

EXPOSE 5000/tcp

ENTRYPOINT ["python"]
CMD ["get-nested.py"]