import argparse
import csv
import os

from collections import Counter
from datetime import datetime

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

    def __init__(self, url, session, data_dir, count_news):
        self.url = url
        self.session = session
        self.data_dir = data_dir
        self.count_news = count_news
        self.stop_words = set(nltk.corpus.stopwords.words('russian'))
        self.stem = Mystem()

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

    def preprocess_text(self, text_news):
        words = [
            word for word in self.stem.lemmatize(text_news.lower())
            if word.isalpha() and word not in self.stop_words
        ]
        return Counter(words)

    def get_words(self):
        counters = []
        for news_url in self.extract_news_urls(self.url):
            text_news = self.extract_text_news(news_url)
            counters.append(Counter(self.preprocess_text(text_news)))
        return sum(counters, Counter())


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

    def save_csv(self, category_name, counter):
        csv_name = os.path.join(self.data_dir, f'{category_name}.csv')
        with open(csv_name, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=('word', 'frequency'))
            writer.writeheader()
            for word, frequency in counter.most_common(self.count_words):
                writer.writerow({'word': word, 'frequency': frequency})

    def exclude_counters_intersection(self, counters):
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
        counters = {}
        for name, category_url in self.extract_categories().items():
            parser = LentaRuParserCategory(
                url=category_url,
                session=self.session,
                data_dir=self.data_dir,
                count_news=self.count_news,
            )
            counters[name] = parser.get_words()

        counters = self.exclude_counters_intersection(counters)

        for name, counter in counters.items():
            self.save_csv(name, counter)


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
