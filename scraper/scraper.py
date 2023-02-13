import shutil
from typing import Optional
from bs4 import BeautifulSoup
import requests
from scraper.globals import MAX_ALOWED_DEPTH
from shutil import rmtree
from os.path import join as join_path, exists as path_exists, basename as path_basename, dirname as path_dirname
from urllib.parse import unquote
from pathlib import Path
from time import sleep


class Scraper:

    def __init__(self, base_url: str, export_path: str, translate: Optional[str] = None, max_depth: int = 0):
        """The init method.

        Arguments:
            base_url (str) -- The specific base URL.
            export_path (str) -- The export path.

        Keyword Arguments:
            translate (str) -- The language to translate (default None)
            max_depth (int) -- The crawl max depth (default 0)
        """
        self._base_url = base_url.strip('/')
        self._export_path = export_path
        self._export_base_path = join_path(self._export_path, 'build')
        self._translate = translate
        self._max_depth = max_depth
        self._sitemap = {}

    def start(self) -> None:
        """The start the scraping
        """
        self._crawl(self._base_url)
        self._export()

    def get_page(self, url: str) -> BeautifulSoup:
        """The get specified page

        Arguments:
            url (str)
        
        Returns:
            BeautifulSoup
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
        }

        counter = 0

        while counter < 3:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                break

            elif response.status_code == 429:
                # Retry on ratelimit
                self._cooldown(20)
                response = requests.get(url, headers=headers)

            counter += 1

        return BeautifulSoup(response.content, 'html.parser')

    def _crawl(self, url: str, current_depth: int = 0) -> None:
        """Crawl the URL.
        
        Arguments:
            url (str) -- The site URL.
            current_depth (int) -- The current crawling depth (default 0).

        Raises:
            Exception
        """
        if current_depth > MAX_ALOWED_DEPTH:
            raise Exception('The maximum allowed depth has been passed.')

        try:
            page = self.get_page(self._refine_link(url))

            self._add_to_sitemap(url, page)

            links = self._extract_links(page)

            for _link in links:

                try:
                    if self._exists_in_sitemap(_link):
                        continue

                    self._add_to_sitemap(_link)

                    if current_depth < self._max_depth:

                        current_depth += 1

                        self._crawl(_link, current_depth)

                except Exception as e:
                    pass

        except Exception as e:
            pass

    def _extract_links(self, page: BeautifulSoup) -> list:
        """Extract the page links

        Arguments:
            page (BeautifulSoup) -- The page.

        Returns:
            list
        """
        return [self._refine_link(link['href']) for link in page.find_all('a', href=True)]

    def _refine_link(self, link: str) -> str:
        """Refine the link to create the relative links.

        Arguments:
            link (str) -- The specified link.

        Returns:
            str
        """
        return f"{self._base_url}/{link.replace(self._base_url, '').strip('/')}".strip('/')

    def _add_to_sitemap(self, url: str, page: Optional[BeautifulSoup] = None) -> None:
        """Add the page to the sitemap

        Arguments:
            url (str) -- The specified URL.

        Keyword Arguments:
            page (BeautifulSoup) -- The page content (default None).
        """
        self._sitemap[url] = page or self.get_page(url)

    def _exists_in_sitemap(self, url: str) -> bool:
        """The exists in the sitemap check.

        Arguments:
            url (str) -- The specified URL.

        Returns:
            bool
        """
        return url in self._sitemap

    def _export(self) -> None:
        """Export the sitemap.
        """
        self._fresh_dir(self._export_base_path)

        for _link, _page in self._sitemap.items():
            self._save_page(_link, _page)
            self._cooldown()

    def _fresh_dir(self, full_path: str) -> None:
        """Remove the specified path.

        Arguments:
            full_path (str) -- The full path to remove.
        """
        self._rmdir(full_path)
        self._mkdir(full_path)

    @staticmethod
    def _rmdir(full_path: str) -> None:
        """Remove the specified path.

        Arguments:
            full_path (str) -- The full path to remove.
        """
        try:
            rmtree(full_path)

        except Exception as e:
            pass

    @staticmethod
    def _mkdir(full_path: str) -> None:
        """Make the specified path.

        Arguments:
            full_path (str) -- The full path to remove.
        """
        path = Path(full_path)
        path.mkdir(parents=True, exist_ok=True)

    def _save_page(self, url: str, page: BeautifulSoup) -> None:
        """Save the page

        Arguments:
            url (str) -- The specified URL.
            page (BeautifulSoup) -- The page.
        """
        file_name = self._get_file_name_by_url(url)
        file_full_path = join_path(self._export_base_path, file_name)

        page_content = self._prepare_page_to_save(page)
        self._mkdir(path_dirname(file_full_path))

        try:
            with open(file_full_path, 'w') as file:
                file.write(page_content)

        except Exception as e:
            print('Can not save the page.')

    def _get_file_name_by_url(self, url: str) -> str:
        """Get the file name by URL.

        Arguments:
            url (str) -- The specified URL.

        Returns:
            str
        """
        file_name = url.replace(self._base_url, '') or 'index'
        return f"{file_name.strip('/')}.html"

    def _prepare_page_to_save(self, page: BeautifulSoup) -> str:
        """Prepare page to save.

        Arguments:
            page (BeautifulSoup) -- The specified page.
        
        Returns:
            str
        """

        page = self._refine_images(page)

        page_content = page.prettify()

        for _font in page_content.split('url(/fonts/')[1:]:
            font_relative_path = f"/fonts/{_font.split(')')[0]}"
            self._download_relative_path(font_relative_path)

        return page_content

    def _refine_images(self, page: BeautifulSoup) -> BeautifulSoup:
        """Refine the images.

        Arguments:
            page (BeautifulSoup) -- The specified page.
        
        Returns:
            BeautifulSoup
        """

        for _image in page.find_all('img'):

            _image['src'] = unquote(_image['src'].replace('https://ccweb.imgix.net/', ''))

            if not _image['src'].startswith(self._base_url):
                _image['src'] = f"{self._base_url}/{_image['src'].strip('/')}"

        for _source in page.find_all('source'):

            if not _source['srcset'].startswith(self._base_url):
                _source['srcset'] = f"{self._base_url}/{_source['srcset'].strip('/')}"

        return page

    def _download_relative_path(self, relative_full_path: str) -> None:
        relative_full_path = relative_full_path.strip('/')

        relative_path = path_dirname(relative_full_path)
        file_name = path_basename(relative_full_path)
        download_base_path = join_path(self._export_base_path, relative_path)

        download_full_path = join_path(download_base_path, file_name)

        if path_exists(download_full_path):
            return

        self._mkdir(download_base_path)

        self._download_file(f"{self._base_url}/{relative_full_path.strip('/')}", download_full_path)

    def _download_file(self, source: str, destination: str):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
        }

        target_file = requests.get(source, headers=headers, stream=True)

        with open(destination, 'wb') as file:
            shutil.copyfileobj(target_file.raw, file)

    @staticmethod
    def _cooldown(sleep_time: int = 1) -> None:
        """Sleep time to cooldown.
        """
        sleep(sleep_time)
