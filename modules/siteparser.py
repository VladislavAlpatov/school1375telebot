from bs4 import BeautifulSoup
import requests


class News:
    """
    Класс для получения новостей
    """
    def __init__(self):
        self.__site = 'https://sch1375u.mskobr.ru'
        self.heard = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
        self.__data = BeautifulSoup(requests.get(self.__site + '/novosti',
                                                 headers=self.heard).text, 'html.parser')

    def get_last_news_title(self):
        """
        Возвращает заголовок последнего блока новостей
        """
        lastnewsblock = self.__data.find('div', {'class': 'kris-news-tit'})
        title = lastnewsblock.find('div', {'class': 'h3'}).text[65:-29]

        return title

    def get_last_news_text(self):
        """
        Возращает текст последего блока новостей
        """
        lastnewsblock = self.__data.find('div', {'class': 'kris-news-tit'})
        data = BeautifulSoup(requests.get(self.__site + lastnewsblock.find('a')['href'],
                                          headers=self.heard).text, 'html.parser')

        return data.find('div', {'class': 'kris-redaktor-format'}).text[:-1]


class Covid19:
    """
    Получает информацию о статистике Covid19
    """
    def __init__(self):
        self.heard = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
        self.__data = BeautifulSoup(requests.get('https://xn--80aesfpebagmfblc0a.xn--p1ai/',
                                                 headers=self.heard).text, 'html.parser').findAll('div', {'class': 'cv-countdown__item-value'})

    def getinfo(self):
        return {'all_infected': self.__data[1].text,
                'last_infected': self.__data[2].text,
                'all_healed': self.__data[3].text,
                'all_died': self.__data[4].text}