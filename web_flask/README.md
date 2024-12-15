# obo-space-web
Это веб-сайт для распространения информации о проекте obo-space.

## Структура проекта

- `main.py` - основной файл для запуска приложения
- `blueprints` - директория для хранения блюпринтов
- `Dockerfile` - файл для сборки Docker-образа
- `requirements.py` - файл для хранения зависимостей

# UML диаграмма

## C4 диаграмма
![C4 диаграмма](resource_readme/c4/IvanovAndrey_C4.png)

## Диаграмма последовательности
<details>
<summary>Диаграмма последовательности</summary>

```plantuml
@startuml
actor Пользователь
participant "Веб-приложение" as Web
participant "Служба аутентификации" as Auth
participant "Служба игр" as Game
participant "Служба уведомлений" as Notify
database "База данных пользователей" as UserDB
database "База данных игр" as GameDB
queue "Очередь сообщений" as MQ
participant "Служба электронной почты" as Email

== Поток веб сайта ==
Пользователь -> Web: Заходит на сайт
Web --> Страница: Отображение страницы

Пользователь -> Web: Нажимает на кнопку "Загрузить игру" 
Web -> Game: Проверка доступности игры
Game --> Web: Ссылка на загрузку
Web --> Пользователь: Загрузка игры

== Поток загрузки игры ==
Пользователь -> Web: Запрос на копию игры
Web -> Game: Проверка доступности игры
Game -> GameDB: Проверка статуса игры
GameDB --> Game: Детали игры
Game -> UserDB: Проверка прав пользователя
UserDB --> Game: Статус пользователя
Game --> Web: Ссылка на загрузку
Web --> Пользователь: Загрузка игры начата

== Поток уведомлений ==
Game -> MQ: Публикация события загрузки
MQ -> Notify: Обработка события
Notify -> Email: Генерация электронной почты
Email -> Пользователь: Отправка подтверждения загрузки

@enduml

```
</details>

![Диаграмма последовательности](data:image/png;base64,dLLDRzD04BsljFzXrNl-059GGI1EGSe1SNPR8oAHjYJEeRSsfXIKGWLKwYrLu0_OhjFcet7-mku_uisiOoUfQo8EiTUhUJDltflTRBSzf-LrcX-aS7QzWvRIrphHKtEkx_2ET62wUaZVKXmYiB7RE7JsFRMbVs8xhEYvETOZFKNiBJPcM0-tbDDMRzsTTSG0QNo4XJfGoEjpvXcU8_C9k0dsFkCzOlopZlU-DC58tvXZ3dtbDDsoK2mYL8h1yHvCBSinGryVU8rtHrBiEPwpuxHT87_e0AsZG8p53FnwvbJfUP4e-DaqRzfkwyNp3TAiaYR8nuxReVY-ETD3Q0cUvboP4zH9T6Y-hj2jrKlx_CQK9gQBF0aLnNFCtCqPDdkSusNJQS1iAQfLzXgj97fIQeYgLgLuR2vKvIcP_KJfAtHAuv2O4uNQw3qofmYEfK00nP6f2BncVX7tEs63kFdkGgKboQGW366jnWNeOc_CXHGMeYfvvSj5PZqimTcIML-_II1IfbIaj4cW7bCAgVx0s3cOVs4EuoM57lY1uQ5XWRjtA39APyVq_jkC2KBdOFqzIvNvGiDOf6nCS4oE3-3ChfUOI46u1RxG6qO4b06D1sl8r9gq-2LFG80HBgfGuZuMWOus6uEqrY1dLOApjJD51sYc1tfSbHLTiSZu6qt0rOgjkIIS4iU0OeE7ur1yX_4iB2IgrLaU7tV1D1zCSs4lan2dgSkVwvCbHQrEU7iN8aSVmQHfoDMjZSiPfB2X1EBR19XVJ8bCoQh-wpQIWi6gNAy-rgd5-McFiMb7u1QIi1Y5ZKcnxUxluS_jBm00)

## ERD диаграмма БД
### Веб-сервер
![ERD диаграмма](resource_readme/erd/web-server.png)

### Локальный сервер игры
![ERD диаграмма](resource_readme/erd/localserver.png)

