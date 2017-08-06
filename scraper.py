import argparse
import asyncio
import collections
import csv
import functools
import itertools
import sys
import time
import threading

import aiohttp
import async_timeout
import tqdm
from bs4 import BeautifulSoup as bs


TIMEOUT = 100

Offer = collections.namedtuple('Offer', 'price year mileage capacity fuel location')


def attribute_error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            value = func(*args, **kwargs)
        except AttributeError:
            return None
        else:
            return value
    return wrapper


class MotoScraper:
    def __init__(self):
        self.lock = threading.Lock()

    def save_to_csv(self, url, filepath):
        offers = self.get_offers(url)
        try:
            with open(filepath, 'wt') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(Offer._fields)
                csv_writer.writerows((offer for offer in offers))
        except OSError:
            raise

        offer_count = len(offers)
        return offer_count

    def get_offers(self, base_url):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        offers = loop.run_until_complete(self._process_all_pages(base_url))
        loop.close()
        return offers

    async def _process_all_pages(self, base_url):
        async with aiohttp.ClientSession() as session:
            all_urls = await self._get_all_urls(session, base_url)
            offer_count = await self._get_offer_count(session, base_url)
            self.progress_bar = tqdm.tqdm(total=offer_count)
            futures = [
                asyncio.ensure_future(self._process_page(session, url))
                for url in all_urls
            ]
            done, _ = await asyncio.wait(futures)

        results = [future.result() for future in done]
        offers = list(itertools.chain.from_iterable(results))
        return offers

    async def _get_all_urls(self, session, base_url):
        page_count = await self._get_page_count(session, base_url)
        page_fmt = '{}&page={}'
        urls = [page_fmt.format(base_url, page_number) for page_number in range(1, page_count + 1)]
        return urls

    async def _get_page_count(self, session, base_url):
        soup = await self._open_page(session, base_url)
        page_spans = soup.findAll("span", {"class": "page"})
        if page_spans:
            page_count = int(''.join(page_spans[-2].stripped_strings))
        else:
            page_count = 1
        return page_count

    async def _get_offer_count(self, session, base_url):
        soup = await self._open_page(session, base_url)
        counters = soup.find(id='tabs-container').findAll("span", {"class": "counter"})
        all_counter = counters[0].text.split()
        all_counter = ''.join(all_counter).strip('()')
        return int(all_counter)

    async def _process_page(self, session, url):
        soup = await self._open_page(session, url)
        offers = soup.findAll("div", {"class": "offer-item__content"})
        processed_offers = list(map(self._process_offer, offers))
        return processed_offers

    async def _open_page(self, session, url):
        try:
            with async_timeout.timeout(TIMEOUT):
                async with session.get(url) as response:
                    html = await response.text()
                    soup = bs(html, 'html.parser').body
                    return soup
        except ValueError:
            raise

    def _process_offer(self, offer_soup):
        offer = Offer(
            price=self._get_price(offer_soup),
            year=self._get_year(offer_soup),
            mileage=self._get_mileage(offer_soup),
            capacity=self._get_capacity(offer_soup),
            fuel=self._get_fuel(offer_soup),
            location=self._get_location(offer_soup)
        )
        with self.lock:
            self.progress_bar.update()
        return offer

    @attribute_error_handler
    def _get_price(self, offer_soup):
        price = offer_soup.find("span", {"class": "offer-price__number"}).text.split()
        price = ''.join(price).replace("PLN", "").replace("EUR", "").split(',')[0]
        return int(price)

    @attribute_error_handler
    def _get_year(self, offer_soup):
        year = offer_soup.find("li", {"class": "offer-item__params-item",
                                      "data-code": "year"}).text.split()
        year = ''.join(year)
        return int(year)

    @attribute_error_handler
    def _get_mileage(self, offer_soup):
        mileage = offer_soup.find("li", {"class": "offer-item__params-item",
                                         "data-code": "mileage"}).text.split()
        mileage = ''.join(mileage).strip("km")
        return int(mileage)

    @attribute_error_handler
    def _get_capacity(self, offer_soup):
        capacity = offer_soup.find("li", {"class": "offer-item__params-item",
                                          "data-code": "engine_capacity"}).text.split()
        capacity = ''.join(capacity).strip("cm3")
        return int(capacity)

    @attribute_error_handler
    def _get_fuel(self, offer_soup):
        fuel = offer_soup.find("li", {"class": "offer-item__params-item",
                                      "data-code": "fuel_type"}).text.split()
        fuel = ''.join(fuel)
        return fuel

    @attribute_error_handler
    def _get_location(self, offer_soup):
        location = offer_soup.find("span", {"class": "offer-item__location"}).text.split()
        location = ''.join(location)
        return location


def main():
    parser = argparse.ArgumentParser(prog='otomoto-scraper',
                                     description='saves offers data as csv in a given filepath')
    parser.add_argument('url')
    parser.add_argument('filepath')
    args = parser.parse_args()

    start = time.time()
    scraper = MotoScraper()
    offer_count = scraper.save_to_csv(args.url, args.filepath)
    end = time.time()

    total_time = round(end - start, 2)
    msg = "\n{} records\nprocessed in: {} sec"
    print(msg.format(offer_count, total_time))


if __name__ == '__main__':
    main()
