from pathlib import Path

from configargparse import ArgParser, Namespace


def parse_arguments() -> Namespace:
    parser = ArgParser(default_config_files=('.env', ))
    parser.add('--fetch_timeout',
               '--FETCH_TIMEOUT',
               type=int,
               default=10,
               help='Fetch timeout for article')
    parser.add('--analysis_timeout',
               '--ANALYSIS_TIMEOUT',
               type=int,
               default=3,
               help='Analysis timeout for article'),
    parser.add('--charged_words_path',
               '--CHARGED_WORDS_PATH',
               type=Path,
               default='./dicts/negative_words.txt',
               help='Path to file with charged words')

    args, _ = parser.parse_known_args()
    return args
