FROM python:3-alpine

MAINTAINER Ashkan Vahidishams "ashkan.vahidishams@sesam.io"

COPY ./service /service
WORKDIR /service

RUN pip install -r requirements.txt

EXPOSE 5000/tcp

ENTRYPOINT ["python"]
CMD ["get-nested.py"]