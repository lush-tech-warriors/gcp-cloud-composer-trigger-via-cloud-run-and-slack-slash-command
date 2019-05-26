# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.7

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY ./app .

# Install production dependencies.
RUN pip3 install --no-cache-dir -r requirements.txt

CMD exec gunicorn --access-logfile - --error-logfile - --log-level debug --bind :$PORT --workers 1 --threads 8 app:__hug_wsgi__
