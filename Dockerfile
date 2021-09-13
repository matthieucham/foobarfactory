FROM python:3.8-slim-buster

ENV APP_PATH=/app \
    APP_USER=fbf \
    LOG_DIR=/logs

COPY requirements.txt /

RUN mkdir $APP_PATH \
    && useradd --system --shell /bin/true --home $APP_PATH $APP_USER \
    && apt-get update \
    && python -m pip install --no-cache-dir -r /requirements.txt \
    && rm -f /requirements.txt \
    && mkdir /logs \
    && chown $APP_USER:$APP_USER /logs

COPY src/ $APP_PATH/

USER $APP_USER
WORKDIR $APP_PATH

ENTRYPOINT ["python"]

CMD ["foobarfactory.py"]
