import csv
import os

from collections import Counter

import nltk

from requests_html import HTMLSession
from pymystem3 import Mystem


try:
    nltk.corpus.stopwords.words('russian')
except LookupError:
    nltk.download('stopwords')


SITE_URL = 'https://lenta.ru'
CSS_CATEGORY_ITEM = '.b-sidebar-menu__list-item'
CSS_NEWS_ITEM = '.row .js-content'
CSS_NEWS_TEXT = '.b-text p'


class LentaRuParserCategory:
    """
    Инкапсулирует логику парсинга текста новостей из определенной категории
    сайта lenta.ru, а также подсчет частотности встречаемых в новостях слов.
    """
    def __init__(self, url, session, count_news):
        self.url = url
        self.session = session
        self.count_news = count_news
        self.stem = Mystem()
        self.stop_words = set(nltk.corpus.stopwords.words('russian'))

    def extract_news_urls(self, category_url, selector=CSS_NEWS_ITEM):
        """
        Извлечь абсолютные ссылки на страницы новостей из определенной
        категории сайта. Возвращает список статей количеством не больше, чем
        значение атрибута `count_news`.

        :param category_url:
            `str`, абсолютная ссылка на страницу со статьями новостей.
        :param selector:
            `str`, css селектор для поиска статей на странице сайта.

        :return:
            `list`, список абсолютных ссылок.
        """
        response = self.session.get(category_url)
        el = response.html.find(selector)
        if not el:
            return []
        news_urls = [i for i in sorted(el[0].absolute_links) if '/news/' in i]
        return news_urls[:self.count_news]

    def extract_text_news(self, news_url, selector=CSS_NEWS_TEXT):
        """
        Извлечь текст статьи по ссылке.

        :param news_url:
            `str`, абсолютная ссылка на страницу новости.
        :param selector:
            `str`, css селектор для извлечения текста статьи на странице.

        :return:
            `str`, текст статьи сайта.
        """
        resp = self.session.get(news_url)
        return ' '.join([i.text for i in resp.html.find(selector)])

    def preprocess_text(self, text_news):
        """
        Выполняет прероцессинг текста статьи:
          - приводит все слова к нижнему регистру;
          - выполняет лемматизацию теста;
          - отбрасывает стоп-слова и пунктуацию;
          - выбирает слова, которые содержат хотя бы один буквенный символ.

        :param text_news:
            `str`, текст статьи.

        :return:
            `list`, список обработанных и отфильтрованных слов статьи.
        """
        return [
            word for word in self.stem.lemmatize(text_news.lower())
            if word.isalpha() and word not in self.stop_words
        ]

    def get_words(self):
        """
        Посчитать количество слов, которые встречаются в текстах новостных
        статьей категории.

        :return:
            `collections.Counter`, счетчик слов.
        """
        counters = []
        for news_url in self.extract_news_urls(self.url):
            text_news = self.extract_text_news(news_url)
            counters.append(Counter(self.preprocess_text(text_news)))
        return sum(counters, Counter())


class LentaRuParserTopWords:
    """
    Инкапсулирует логику извлечения и сохранения частотности слов в новостных
    статьях всех категорий сайта lenta.ru, которые представлены на главной
    странице.
    """
    def __init__(self, count_words, data_dir, count_news, url=SITE_URL):
        self.url = url
        self.session = HTMLSession()
        self.count_words = count_words
        self.data_dir = data_dir
        self.count_news = count_news

    def extract_categories(self, selector=CSS_CATEGORY_ITEM):
        """
        Извлечь абсолютные ссылки на страницы категорий/рубрик сайта.

        :param selector:
            `str`, css селектор для поиска категорий на главной странице сайта.

        :return:
            `list`, список абсолютных ссылок.
        """
        resp = self.session.get(self.url)
        categories = {}
        for el in resp.html.find(selector):
            if not el.absolute_links:
                continue
            link = el.absolute_links.pop()
            if '/rubrics/' in link:
                name = link.rstrip('/').rsplit('/', 1)[-1]
                categories[name] = link
        return categories

    def save_csv(self, category_name, counter):
        """
        Сохранить результат подсчета частотности слов для категории в csv файл.

        :param category_name:
            `str`, наименование категории.
        :param counter:
            `collections.Counter`, счетчик слов.
        """
        csv_name = os.path.join(self.data_dir, f'{category_name}.csv')
        with open(csv_name, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=('word', 'frequency'))
            writer.writeheader()
            for word, frequency in counter.most_common(self.count_words):
                writer.writerow({'word': word, 'frequency': frequency})

    @staticmethod
    def exclude_counters_intersection(counters):
        """
        Исключить повторение слов в счетчиках частотности для категорий.
        Для слова выбирается та категория, где оно встречается чаще всего. Если
        частота между категориями равна, то выбирается первая из списка.

        :param counters:
            `dict`, словарь, в котором ключом является наименование категории,
            а значение это счетчик частотности слов в этой категории.
        :return:
            `dict`, словарь категорий для которых удалены пересечения в топах
        """
        max_counter = Counter()
        for counter in counters.values():
            max_counter = max_counter | counter

        result = {}
        already_use = set()
        for name, counter in counters.items():
            new_counter = Counter()
            for word, count in counter.items():
                if count == max_counter[word] and word not in already_use:
                    new_counter[word] = count
                    already_use.add(word)
            result[name] = new_counter

        return result

    def run(self):
        """
        Метод выполняет:
            - извлечение абсолютных ссылок на категории сайта;
            - получение частотности слов в новостях категорий;
            - сохранение частотности в csv-файлы.
        """
        counters = {}
        for name, category_url in self.extract_categories().items():
            parser = LentaRuParserCategory(
                url=category_url,
                session=self.session,
                count_news=self.count_news,
            )
            counters[name] = parser.get_words()

        counters = self.exclude_counters_intersection(counters)

        for name, counter in counters.items():
            self.save_csv(name, counter)
