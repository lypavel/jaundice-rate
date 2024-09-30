# Фильтр желтушных новостей

Набор скриптов, который позволяет морфологически анализировать статью и на основе встречающихся в ней слов формировать её "рейтинг желтушности".

Алгоритм анализа:
1. Текст статьи скачивается и очищается от HTML-тегов.
2. Текст морфологически разбивается на отдельные слова.
3. На основе того, как много эмоционально окрашенных слов содержится в статье, формируется её рейтинг.
4. Информация об анализе статьи отображается в терминале.

Пока поддерживается только один новостной сайт - [ИНОСМИ.РУ](https://inosmi.ru/). Для него разработан специальный адаптер, умеющий выделять текст статьи на фоне остальной HTML разметки. Для других новостных сайтов потребуются новые адаптеры, все они будут находиться в каталоге `adapters`. Туда же помещен код для сайта ИНОСМИ.РУ: `adapters/inosmi_ru.py`.

В перспективе можно создать универсальный адаптер, подходящий для всех сайтов, но его разработка будет сложной и потребует дополнительных времени и сил.

# Как установить

1. Установите Python 3.10.12
2. Создайте виртуальное окружение:
    ```bash
    python3 -m venv venv
    ```
3. Установите необходимые для работы зависимости:
    ```bash
    pip install -r requirements.txt
    ```
4. (опционально) Объявите в файле `.env` необходимые вам настройки:
    ```env
    SERVER_HOST=0.0.0.0                              # Хост сервера
    SERVER_PORT=8080                                 # Порт сервера
    FETCH_TIMEOUT=10                                 # тайм-аут для скачивания текста статьи
    ANALYSIS_TIMEOUT=3                               # тайм-аут для анализа текста статьи
    CHARGED_WORDS_PATH='./dicts/negative_words.txt'  # путь к словарю с заряженными словами
    ```

    Также эти настройки можно передать при запуске скрипта с помощью одноименных аргументов.

# Как запустить сервер

```bash
python3 server.py
```

### Отправка запросов на сервер

```bash
http://<server_host>:<server_port>?articles=<article1_url>,<article2_url>,<article3_url>
```



# Как запустить тесты

Для тестирования используется [pytest](https://docs.pytest.org/en/latest/), тестами покрыты фрагменты кода сложные в отладке: `text_tools.py`, `articles.py` и адаптеры.

Для удобства запуска все тесты перенесены в директорию `./tests/`

### Запустить все тесты

```bash
python3 -m pytest ./tests/ -vv
```

### Запуск отдельных тестов

```bash
python3 -m pytest ./tests/<test_name>.py -vv
```

# Цели проекта

Код написан в учебных целях. Это урок из курса по веб-разработке — [Девман](https://dvmn.org).
