FROM python:3-stretch
RUN pip3 install pipenv
WORKDIR /usr/src/app
COPY . .
RUN pip install pip==18.0
RUN pipenv install --system
CMD [ "python", "./bot.py" ]