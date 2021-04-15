FROM python:3.9-buster
RUN apt-get update && apt-get install -y \
  python3-pip

COPY ./crawler/ /var/lib/
COPY ./requirements.txt /var/lib/crawler/

RUN pip3 install -r /var/lib/crawler/requirements.txt
RUN pip3 install psycopg2

CMD python3 /var/lib/crawler/main.py