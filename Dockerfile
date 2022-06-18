FROM python:3.9-slim-bullseye

ARG APP_HOME=/app
WORKDIR ${APP_HOME}
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential
COPY . .
RUN chmod +x ./start
RUN pip install -r requirements.txt
