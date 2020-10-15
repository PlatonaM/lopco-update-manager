FROM python:3-alpine

RUN apk update && apk upgrade && apk add git

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "--workers", "1", "--threads", "4", "--worker-class", "gthread", "--log-level", "error", "app:app"]
