from bs4 import BeautifulSoup
import requests


class News:
    """
    Парсит с https://citaty.info/random всякие цитаты
    """
    def __init__(self):
        self.__site = 'https://sch1375u.mskobr.ru'
        self.heard = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
        self.__data = BeautifulSoup(requests.get(self.__site + '/novosti',
                                                 headers=self.heard).text, 'html.parser')

    def getLastNewsTitle(self):
        latsnewsblock = self.__data.find('div', {'class': 'kris-news-tit'})
        title = latsnewsblock.find('div', {'class': 'h3'}).text[65:-29]
        return title

    def getLastNewsText(self):
        latsnewsblock = self.__data.find('div', {'class': 'kris-news-tit'})
        data = BeautifulSoup(requests.get(self.__site + latsnewsblock.find('a')['href'],
                                          headers=self.heard).text, 'html.parser')
        return data.find('div', {'class': 'kris-redaktor-format'}).text[:-1]


class Jokes:
    """
    Парсит с сайта https://nekdo.ru/random/ всякие шутки
    """
    def __init__(self):
        self.heard = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
        self.__data = BeautifulSoup(requests.get('https://nekdo.ru/random/', headers=self.heard).text, 'html.parser')

    def getJoke(self):
        return self.__data.find('div', {'class': 'text'}).text
