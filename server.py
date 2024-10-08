import asyncio
from functools import partial
import logging
from pathlib import Path

from aiohttp import ClientSession, web
from aiohttp.web_request import Request
import anyio
from anyio import create_task_group
from pymorphy2 import MorphAnalyzer

from articles import process_article
from parse_args import parse_arguments
from text_tools import load_charged_words

logger = logging.getLogger(Path(__file__).name)


async def handle(request: Request,
                 morph: MorphAnalyzer,
                 charged_words: list[str],
                 fetch_timeout: int,
                 analysis_timeout: int) -> list:
    articles_param = request.query.get('articles', None)
    if not articles_param:
        return web.json_response({})

    article_urls = articles_param.split(',')

    if len(article_urls) > 10:
        return web.json_response(
            {'error': 'too many urls in request, should be 10 or less'},
            status=400,
        )

    articles = []

    async with ClientSession() as session:
        async with create_task_group() as task_group:
            for article_url in article_urls:
                task_group.start_soon(
                    process_article,
                    session,
                    morph,
                    article_url,
                    charged_words,
                    articles,
                    fetch_timeout,
                    analysis_timeout
                )

    response = [{'status': article.status.value,
                 'url': article.url,
                 'score': article.score,
                 'words_count': article.words_count} for article in articles]
    return web.json_response(response)


async def start_server(host: str, port: int, handler: partial):
    app = web.Application()
    app.add_routes([web.get('/', handler)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    logger.info(f'Started web server at http://{host}:{port}')

    await anyio.sleep_forever()


async def main():
    logging.basicConfig(
        level=logging.INFO
    )

    args = parse_arguments()

    morph = MorphAnalyzer()
    charged_words = await load_charged_words(args.charged_words_path, morph)
    handle_article = partial(handle, morph=morph,
                             charged_words=charged_words,
                             fetch_timeout=args.fetch_timeout,
                             analysis_timeout=args.analysis_timeout)

    async with create_task_group() as tg:
        tg.start_soon(start_server,
                      args.server_host,
                      args.server_port,
                      handle_article)


if __name__ == '__main__':
    asyncio.run(main())
