from scraper.app import ScraperApp
from scraper.logger import Logger
from argparse import ArgumentParser


def main():
    Logger.setup()
    app = ScraperApp()
    args = validate_args()
    app.run(args)


def validate_args() -> dict:
    """Validate the args.

    Returns:
        dict
    """
    args_parser = ArgumentParser(add_help=False)

    args_parser.add_argument(
        '--base-url',
        help='The specified base URL.',
        required=True
    )

    args_parser.add_argument(
        '--export-path',
        help='The export path.',
        required=True
    )

    args_parser.add_argument(
        '--translate',
        help='The specified language to translate.'
    )

    return vars(args_parser.parse_args())


if __name__ == '__main__':
    main()
