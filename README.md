# backendschool2022RESTAPI
Вступительное задание в Осеннюю Школу Бэкенд Разработки Яндекса 2022. Разработать бэкенд для веб-сервиса хранения файлов, аналогичный сервису Яндекс Диск.

###Контейнер на удаленном сервере  разворачивается на основе репозитория GitHub

```
git@github.com:rusnikolaev1/backendschool2022RESTAPI.git
cd backendschool2022RESTAPI
touch .env
nano .env
```
В .env файле нужно указать следующее

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=marketdb
POSTGRES_USER=postgres # В docker-compose.yaml и здесь имена пользователя БД должны совпадать
POSTGRES_PASSWORD=postgres_password # В docker-compose.yaml и здесь пароли должны совпадать
DB_HOST= db
DB_PORT=5432
SECRET_KEY=foo # Секретный ключ для Django settings.py
DJANGO_DEBUG=0 
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1] 10.21.2.43 0.0.0.0 127.0.0.1 #Добавьте еще, если надо
```

Формируем контейнер
```
sudo docker-compose -f docker-compose.yaml up -d --build
sudo docker-compose -f docker-compose.yaml exec web python manage.py makemigrations
sudo docker-compose -f docker-compose.yaml exec web python manage.py migrate --run-syncdb
```