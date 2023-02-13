from .scraper import Scraper


class ScraperApp:

    @staticmethod
    def run(args: dict) -> None:
        """Run the application

        Arguments:
            args (dict)
        """
        scraper = Scraper(
            base_url=args.get('base_url'),
            translate=args.get('translate'),
            export_path=args.get('export_path')
        )

        scraper.start()
