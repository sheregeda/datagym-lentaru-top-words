import argparse
import csv
import string
import nltk
import os
import operator

from collections import Counter
from datetime import datetime

from requests_html import HTMLSession

from pprint import pprint

try:
    nltk.corpus.stopwords.words('russian')
except LookupError:
    nltk.download('stopwords')


SITE_URL = 'https://lenta.ru'
CSS_CATEGORY_ITEM = '.b-sidebar-menu__list-item'
CSS_NEWS_ITEM = '.row .js-content'
CSS_NEWS_TEXT = '.b-text p'


class LentaRuParserCategory:

    def __init__(self, url, name, session, data_dir, count_news):
        self.url = url
        self.name = name
        self.session = session
        self.data_dir = data_dir
        self.count_news = count_news
        self.words = None
        self.stop_words = set(nltk.corpus.stopwords.words('russian'))

    def extract_news_urls(self, category_url, selector=CSS_NEWS_ITEM):
        resp = self.session.get(category_url)
        news_urls = [
            i for i in resp.html.find(selector)[0].absolute_links
            if '/news/' in i
        ]
        return news_urls[:self.count_news]

    def extract_text_news(self, news_url, selector=CSS_NEWS_TEXT):
        resp = self.session.get(news_url)
        return ' '.join([i.text for i in resp.html.find(selector)])

    def count_words(self, text_news):
        words = []
        for word in text_news.split():
            word = word.strip(string.punctuation + '—').lower()
            if not word or word.isdigit() or word in self.stop_words:
                continue
            words.append(word)
        return Counter(words)

    def fill_words(self):
        counters = []
        for news_url in self.extract_news_urls(self.url):
            text = self.extract_text_news(news_url)
            counters.append(self.count_words(text))
        self.words = sum(counters, Counter())

    def save_csv(self, count_words):
        with open(os.path.join(self.data_dir, f'{self.name}.csv'), 'w') as f:
            writer = csv.DictWriter(f, fieldnames=('word', 'frequency'))
            writer.writeheader()
            for word, frequency in self.words.most_common(count_words):
                writer.writerow({'word': word, 'frequency': frequency})


class LentaRuParserTopWords:
    def __init__(self, count_words, data_dir, count_news, url=SITE_URL):
        self.url = url
        self.session = HTMLSession()
        self.count_words = count_words
        self.data_dir = data_dir
        self.count_news = count_news

    def extract_categories(self, selector=CSS_CATEGORY_ITEM):
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

    def exclude_parsers_intersection(self, parsers):
        max_counter = Counter()
        for parser in parsers:
            max_counter = max_counter | parser.words
        already_use = set()
        for parser in parsers:
            counter = Counter()
            for word, count in parser.words.items():
                if max_counter[word] <= count and word not in already_use:
                    counter[word] = count
                    already_use.add(word)
            parser.words = counter

    def run(self):
        parsers = []
        for name, category_url in self.extract_categories().items():
            parser = LentaRuParserCategory(
                url=category_url,
                name=name,
                session=self.session,
                data_dir=self.data_dir,
                count_news=self.count_news,
            )
            parser.fill_words()
            parsers.append(parser)

        self.exclude_parsers_intersection(parsers)

        for parser in parsers:
            parser.save_csv(self.count_words)


def main():
    parser = argparse.ArgumentParser(
        add_help=True,
        description='Скрипт для оценки частотности слов в новостях lenta.ru.'
    )
    parser.add_argument(
        '-d', '--data-dir', type=str, default='./data', required=False,
        help='Каталог для сохранения результата.'
    )
    parser.add_argument(
        '-w', '--count-words', type=int, default=20, required=False,
        help='Количество топовых слов для категории сайта, которое требуется '
             'получить.'
    )
    parser.add_argument(
        '-n', '--count-news', type=int, default=10, required=False,
        help='Максимальное количество статьей в категории сайта, которое '
             'требуется проанализировать. Но не больше, чем всего статей на '
             'первой странице категории.'
    )
    args = parser.parse_args()
    data_dir = os.path.join(
        args.data_dir, datetime.now().strftime('%Y%d%m_%H%M%S')
    )
    os.makedirs(data_dir, exist_ok=True)
    parser = LentaRuParserTopWords(
        data_dir=data_dir,
        count_words=args.count_words,
        count_news=args.count_news,
    )
    parser.run()


if __name__ == '__main__':
    main()
