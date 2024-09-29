import asyncio
import aiohttp
from pathlib import Path
import pytest
from unittest.mock import patch

from pymorphy2 import MorphAnalyzer

from main import process_article, load_charged_words, ProcessingStatus

# FETCH_TIMEOUT = 10
# ANALYSIS_TIMEOUT = 3

FETCH_ERROR_URL = 'https://inosmi.ru/not/exist.html'
PARSING_ERROR_URL = 'https://lenta.ru/brief/2021/08/26/afg_terror/'


@pytest.mark.asyncio
async def test_process_article():
    morph = MorphAnalyzer()
    charged_words = load_charged_words(Path('negative_words.txt'), morph)

    articles = []

    async with aiohttp.ClientSession() as session:
        await process_article(session,
                              morph,
                              FETCH_ERROR_URL,
                              charged_words,
                              articles)

        article = articles[0]
        assert (article.status, article.words_count, article.score) == (ProcessingStatus.FETCH_ERROR, None, None)
        articles.pop(0)

        await process_article(session,
                              morph,
                              PARSING_ERROR_URL,
                              charged_words,
                              articles)

        article = articles[0]
        assert (article.status, article.words_count, article.score) == (ProcessingStatus.PARSING_ERROR, None, None)
        articles.pop(0)

        await process_article(session,
                              morph,
                              PARSING_ERROR_URL,
                              charged_words,
                              articles)

        article = articles[0]
        assert (article.status, article.words_count, article.score) == (ProcessingStatus.PARSING_ERROR, None, None)
        articles.pop(0)

        await process_article(session,
                              morph,
                              PARSING_ERROR_URL,
                              charged_words,
                              articles)

        article = articles[0]
        assert (article.status, article.words_count, article.score) == (ProcessingStatus.PARSING_ERROR, None, None)
        articles.pop(0)
