FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/bin/
RUN chmod +x /usr/bin/wait-for-it.sh

ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD requirements-test.txt /code/
RUN pip install -r requirements-test.txt
