import asyncio
from aiohttp import ClientSession
import pytest
from unittest.mock import patch

from pymorphy2 import MorphAnalyzer

from articles import process_article, ProcessingStatus
from parse_args import parse_arguments
from text_tools import load_charged_words

FETCH_ERROR_URL = 'https://inosmi.ru/not/exist.html'
PARSING_ERROR_URL = 'https://lenta.ru/brief/2021/08/26/afg_terror/'
CORRECT_URL = 'https://inosmi.ru/20240629/assanzh-269370889.html'

ARGS = parse_arguments()
MORPH = MorphAnalyzer()
CHARGED_WORDS = load_charged_words(ARGS.charged_words_path, MORPH)
FETCH_TIMEOUT = ARGS.fetch_timeout
ANALYSIS_TIMEOUT = ARGS.analysis_timeout


@pytest.mark.asyncio
async def test_success_case():
    articles = []
    async with ClientSession() as session:
        await process_article(session,
                              MORPH,
                              CORRECT_URL,
                              CHARGED_WORDS,
                              articles,
                              FETCH_TIMEOUT,
                              ANALYSIS_TIMEOUT)

    article = articles[0]

    assert article.status == ProcessingStatus.OK
    assert article.words_count == 685
    assert article.score == 1.46


@pytest.mark.asyncio
async def test_fetch_error():
    articles = []

    async with ClientSession() as session:
        await process_article(session,
                              MORPH,
                              FETCH_ERROR_URL,
                              CHARGED_WORDS,
                              articles,
                              FETCH_TIMEOUT,
                              ANALYSIS_TIMEOUT)

        article = articles[0]

        assert article.status == ProcessingStatus.FETCH_ERROR
        assert article.words_count is None
        assert article.score is None


@pytest.mark.asyncio
async def test_parsing_error():
    articles = []
    async with ClientSession() as session:
        await process_article(session,
                              MORPH,
                              PARSING_ERROR_URL,
                              CHARGED_WORDS,
                              articles,
                              FETCH_TIMEOUT,
                              ANALYSIS_TIMEOUT)

        article = articles[0]

        assert article.status == ProcessingStatus.PARSING_ERROR
        assert article.words_count is None
        assert article.score is None


@pytest.mark.asyncio
async def test_fetch_timeout():
    articles = []
    async with ClientSession() as session:
        await process_article(session,
                              MORPH,
                              CORRECT_URL,
                              CHARGED_WORDS,
                              articles,
                              0,
                              ANALYSIS_TIMEOUT)

        article = articles[0]

        assert article.status == ProcessingStatus.TIMEOUT
        assert article.words_count is None
        assert article.score is None


@pytest.mark.asyncio
async def test_analysis_timeout():
    articles = []
    with patch('articles.sanitize', side_effect=asyncio.TimeoutError):
        async with ClientSession() as session:
            await process_article(session,
                                  MORPH,
                                  CORRECT_URL,
                                  CHARGED_WORDS,
                                  articles,
                                  FETCH_TIMEOUT,
                                  0)

            article = articles[0]

            assert article.status == ProcessingStatus.TIMEOUT
            assert article.words_count is None
            assert article.score is None
