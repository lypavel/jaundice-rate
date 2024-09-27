import aiohttp
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import time

from anyio import create_task_group
from async_timeout import timeout
from pymorphy2 import MorphAnalyzer

from adapters.exceptions import ArticleNotFound
from adapters.inosmi_ru import sanitize
from text_tools import split_by_words, calculate_jaundice_rate


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


@dataclass
class Article():
    url: str
    status: ProcessingStatus
    words_count: int = None
    score: float = None
    analysys_duration: float = 0

    def __str__(self):
        return (
            '\n'
            f'URL: {self.url}\n'
            f'Статус: {self.status.value}\n'
            f'Рейтинг: {self.score}\n'
            f'Слов в статье: {self.words_count}'
        )


TEST_ARTICLES = [
    'https://lenta.ru/brief/2021/08/26/afg_terror/',
    'https://inosmi.ru/not/exist.html',
    'https://inosmi.ru/20240926/berbok-270222878.html',
    'https://inosmi.ru/20240927/zelenskiy-270236865.html',
    'https://inosmi.ru/20240927/kharris-270235080.html',
    'https://inosmi.ru/20240927/turtsiya-270237489.html',
    'https://inosmi.ru/20240927/rossiya-270239278.html',
    'http://inosmi.ru/economic/20190629/245384784.html'
]

logger = logging.getLogger(Path(__file__).name)


@asynccontextmanager
async def timer():
    start_time = time.monotonic()
    yield lambda: time.monotonic() - start_time


async def fetch(session, url):
    try:
        async with timeout(10):
            async with session.get(url) as response:
                response.raise_for_status()
                return ProcessingStatus.OK, await response.text()
    except aiohttp.ClientError:
        return ProcessingStatus.FETCH_ERROR, None
    except asyncio.TimeoutError:
        return ProcessingStatus.TIMEOUT, None


async def process_article(session, morph: MorphAnalyzer, article_url, negative_words, articles):
    status, html = await fetch(session, article_url)
    if not html:
        articles.append(Article(article_url, status))
        return

    async with timer() as get_elapsed_time:
        try:
            cleaned_data = sanitize(html, plaintext=True)
        except ArticleNotFound:
            articles.append(Article(article_url, ProcessingStatus.PARSING_ERROR))
            return

        article_words = split_by_words(morph, cleaned_data)
        article_rating = calculate_jaundice_rate(article_words, negative_words)
        duration = get_elapsed_time()
        articles.append(
            Article(article_url, status, len(article_words), article_rating, duration)
        )


async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    morph = MorphAnalyzer()
    with open('negative_words.txt', 'r') as stream:
        data = stream.read()
    negative_words = split_by_words(morph, data)

    articles = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for article_url in TEST_ARTICLES:
                task_group.start_soon(
                    process_article,
                    session,
                    morph,
                    article_url,
                    negative_words,
                    articles
                )

    for article in articles:
        print(article)
        logger.info(f'Анализ закончен за {article.analysys_duration:.2f} сек')


if __name__ == '__main__':
    asyncio.run(main())
