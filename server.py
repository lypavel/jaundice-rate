from functools import partial
from pathlib import Path

import aiohttp
from aiohttp import web
from aiohttp.web_request import Request
from anyio import create_task_group
from pymorphy2 import MorphAnalyzer

from main import load_charged_words, process_article


async def handle(request: Request,
                 morph: MorphAnalyzer,
                 charged_words: list[str]) -> list:
    article_urls = request.query.get('articles', None)
    if not article_urls:
        return web.json_response({})

    if len(article_urls) > 10:
        return web.json_response(
            {'error': 'too many urls in request, should be 10 or less'},
            status=400,
        )

    articles = []

    async with aiohttp.ClientSession() as session:
        async with create_task_group() as task_group:
            for article_url in article_urls.split(','):
                task_group.start_soon(
                    process_article,
                    session,
                    morph,
                    article_url,
                    charged_words,
                    articles
                )

    response = [{'status': article.status.value,
                 'url': article.url,
                 'score': article.score,
                 'words_count': article.words_count} for article in articles]
    return web.json_response(response)


def main():
    morph = MorphAnalyzer()
    charged_words = load_charged_words(Path('negative_words.txt'), morph)
    handle_article = partial(handle, morph=morph, charged_words=charged_words)

    app = web.Application()
    app.add_routes([web.get('/', handle_article)])

    web.run_app(app, port=8000)


if __name__ == '__main__':
    main()
