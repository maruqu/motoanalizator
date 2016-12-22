from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from http.client import IncompleteRead
from urllib.error import URLError
from queue import Queue
from time import time
import math
from sys import argv
import string
import concurrent.futures
from itertools import repeat


def main():
    start = time()
    scraper = MotoScraper(argv[1])
    data = scraper.data
    end = time()

    for record in data:
        print(record)

    print(
        "\n{0} records, processed in: {1} sec\n"
        .format(
            str(len(data)),
            str(round(end - start, 2))
        )
    )


class MotoScraper(object):

    def __init__(self, url):
        """Start scraping"""
        self.__start_threads(url)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value

    def __start_threads(self, url):
        """Start threads to process all subpages"""

        page_count = self.__get_page_count(url)

        urls = []
        for i in range(1, page_count + 1):
            urls.append(url + "&page=" + str(i))

        queue = Queue()

        with concurrent.futures.ThreadPoolExecutor(max_workers=page_count) as executor:
            executor.map(self.__process_subpage, urls, repeat(queue))

        self.data = list(queue.queue)

    def __process_subpage(self, url, queue):
        """Get offers data from page and put in queue"""

        soup = self.__open_page(url)
        # more efficient to reduce the scope of search
        offers = soup.find("div", {"class": "offers list"})
        items = offers.findAll("div", {"class": "offer-item__content"})

        for item in items:

            price = self.__find_price(item)
            year, milage, capacity, fuel = self.__find_details(item)
            location = self.__find_location(item)

            record = (price, year, milage, capacity, fuel, location)
            queue.put(record)

    def __get_page_count(self, url):
        """Return the number of subpages"""

        soup = self.__open_page(url)
        page_spans = soup.findAll("span", {"class": "page"})

        if len(page_spans) != 0:  # If only one page len = 0
            page_count = int(''.join(page_spans[-2].stripped_strings))
        else:
            page_count = 1

        return page_count

    def __open_page(self, url):
        """Return souf of page body"""

        while True:     # In case of urllib exception try unless success
            try:
                response = urlopen(url)
                soup = bs(response.read(), 'html.parser').body
            except (IncompleteRead, URLError):
                continue
            break

        return soup

    def __find_price(self, item):
        """Get price"""
        # TODO from eur to pln
        price = item.find(
            "span", {"class": "offer-price__number"}).stripped_strings
        price = ''.join(price).replace("PLN", "").replace("EUR", "") \
                .replace(",", ".").replace(" ", "")

        return int(price)

    def __find_location(self, item):
        """Return only province"""
        location = item.find("span", {"class": "offer-item__location"})
        location_stripped = [string for string in location.stripped_strings][-1][1:-1]

        return location_stripped

    def __find_details(self, item):
        """Find year, milage, capacity and fuel type of vehicle"""

        details = item.find("ul", {"class": "offer-item__params"})
        paramList = details.findAll("li", {"class": "offer-item__params-item"})

        if len(paramList) == 4:
            year = int(''.join(paramList[0].text.split()))
            milage = int(''.join(paramList[1].text.split())[:-2:])
            capacity = int(''.join(paramList[2].text.split())[:-3:])
            fuel = ''.join(paramList[3].text.split())

        else:  # Sometimes not every parameter given
            year = int(''.join(paramList[0].text.split()))

            if "km" not in ''.join(paramList[1].text.split()):
                milage = 0
                if "cm3" not in ''.join(paramList[1].text.split()):
                    capacity = 0
                else:
                    capacity = int(''.join(paramList[1].text.split())[:-3:])
            else:
                milage = int(''.join(paramList[1].text.split())[:-2:])
                if "cm3" not in ''.join(paramList[2].text.split()):
                    capacity = 0
                else:
                    capaity = int(''.join(paramList[2].text.split())[:-3:])

            fuel = ''.join(paramList[-1].text.split())

        return (year, milage, capacity, fuel)


if __name__ == '__main__':
    main()
