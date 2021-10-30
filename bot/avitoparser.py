from logging import log, WARNING

import requests
from bs4 import BeautifulSoup

from config.config import AVITO_HEADERS, AVITO_URL
from config.htmlclass import A_CLASS, DIV_CLASS, SPAN_CLASS


class Base:
    BASE_URL = AVITO_URL

    HEADERS = AVITO_HEADERS

    def city(self, city):
        self.city = city
        return self

    def min_price(self, min_price):
        self.min_price = min_price
        return self

    def max_price(self, max_price):
        self.max_price = max_price
        return self

    def search_object(self, search_object):
        self.search_object = search_object
        return self


class Avito(Base):
    def get(self):
        self.response = requests.get(
            self.BASE_URL +
            f'{str(self.city) + "?"}'
            f'{"pmin=" + str(self.min_price)}'
            f'{"&pmax=" + str(self.max_price)}'
            f'{"&q=" + str(self.search_object)}',
            headers=self.HEADERS
        )
        return self

    def parse(self):
        soup = BeautifulSoup(self.response.text, 'lxml')
        price = soup.find_all('span', class_=SPAN_CLASS)
        text = soup.find_all('div', class_=DIV_CLASS)
        link = soup.find_all('a', href=True, class_=A_CLASS)
        result = [
            [price[i].text.replace(u'\xa0', ' ').replace(u'\u2009', ''),
             self.BASE_URL + link[i]['href']] for i in range(0, len(link))
        ]
        try:
            [result[i].append(text[i].text) for i in range(0, len(result[0]))]
        except IndexError as e:
            log(level=WARNING, msg=(e, result))
        return result