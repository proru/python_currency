# python_currency
python currency getting aiohttp

docker login - для подключения к репозиторию docker hub.docker.com

bash run.sh build - сборка image
bash run.sh up - поднятие контейнера с сервером на порту 8080
bash run.sh stop остановить контейнер
bash run.sh rebuild пересобрать image 


локальный запуск 
python version 3.9.2
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -U wheel
pip install -U setuptools 
pip install -r /app/requirements.txt

--запустить скрипт на порту 8080 
python3 rest_framework.py --debug 1 --usd 10 --rub 20 --eur 30 --period 60
