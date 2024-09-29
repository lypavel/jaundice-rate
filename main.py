import aiohttp
from aiohttp.client import ClientSession
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import sys
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
    analysis_duration: float = 0

    def __str__(self):
        return (
            '\n'
            f'URL: {self.url}\n'
            f'Статус: {self.status.value}\n'
            f'Рейтинг: {self.score}\n'
            f'Слов в статье: {self.words_count}'
        )


TEST_ARTICLES = [
    'https://lenta.ru/brief/2021/08/26/afg_terror/',  # PARSING_ERROR
    'https://inosmi.ru/not/exist.html',               # FETCH ERROR
    'https://inosmi.ru/20240926/berbok-270222878.html',
    'https://inosmi.ru/20240927/zelenskiy-270236865.html',
    'https://inosmi.ru/20240927/kharris-270235080.html',
    'https://inosmi.ru/20240927/turtsiya-270237489.html',
    'https://inosmi.ru/20240927/rossiya-270239278.html',
    'https://inosmi.ru/20240629/assanzh-269370889.html',
]

FETCH_TIMEOUT = 10
ANALYSIS_TIMEOUT = 3

logger = logging.getLogger(Path(__file__).name)


@asynccontextmanager
async def timer():
    start_time = time.monotonic()
    yield lambda: time.monotonic() - start_time


async def fetch(session: ClientSession, url: str) -> str:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session: ClientSession,
                          morph: MorphAnalyzer,
                          article_url: str,
                          charged_words: list[str],
                          articles: list) -> None:
    try:
        async with timeout(FETCH_TIMEOUT):
            html = await fetch(session, article_url)

        cleaned_data = sanitize(html, plaintext=True)

        async with timer() as get_elapsed_time:
            async with timeout(ANALYSIS_TIMEOUT):
                article_words = split_by_words(morph, cleaned_data)

            article_score = calculate_jaundice_rate(article_words,
                                                    charged_words)

        duration = get_elapsed_time()

        articles.append(
            Article(url=article_url,
                    status=ProcessingStatus.OK,
                    words_count=len(article_words),
                    score=article_score,
                    analysis_duration=duration)
        )
    except aiohttp.ClientError:
        articles.append(Article(url=article_url,
                                status=ProcessingStatus.FETCH_ERROR))
    except asyncio.TimeoutError:
        articles.append(Article(url=article_url,
                                status=ProcessingStatus.TIMEOUT))
    except ArticleNotFound:
        articles.append(Article(url=article_url,
                                status=ProcessingStatus.PARSING_ERROR))


def load_charged_words(file_path: Path,
                       morph: MorphAnalyzer) -> list[str]:
    with open(file_path, 'r') as stream:
        data = stream.read()
    charged_words = split_by_words(morph, data)
    return charged_words


async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    morph = MorphAnalyzer()
    charged_words = load_charged_words(Path('negative_words.txt'), morph)

    articles = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for article_url in TEST_ARTICLES:
                task_group.start_soon(
                    process_article,
                    session,
                    morph,
                    article_url,
                    charged_words,
                    articles
                )

    for article in articles:
        print(article, file=sys.stdout)
        logger.info(f'Анализ закончен за {article.analysis_duration:.2f} сек')


if __name__ == '__main__':
    asyncio.run(main())
