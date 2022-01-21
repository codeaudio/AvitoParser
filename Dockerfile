FROM python:3.8.5
WORKDIR /code
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./
RUN python manage.py collectstatic --noinput
CMD [ "python", "/code/bot/bot.py" ]
CMD python manage.py migrate --run-syncdb
CMD gunicorn avito.wsgi:application --bind 0.0.0.0:8000