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


class Covid19:
    def __init__(self):
        self.heard = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'}
        self.__data = BeautifulSoup(requests.get('https://xn--80aesfpebagmfblc0a.xn--p1ai/',
                                                 headers=self.heard).text, 'html.parser')
        self.__blocks = self.__data.findAll('div', {'class': 'cv-countdown__item-value'})

    def getAllInfected(self):
        return self.__blocks[1].text

    def getInfectedInLastDay(self):
        return self.__blocks[2].text

    def getAllHealed(self):
        return self.__blocks[3].text

    def getAllDied(self):
        return self.__blocks[4].text
