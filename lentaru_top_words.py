import argparse
import csv

from requests_html import HTMLSession


SITE_URL = 'https://lenta.ru'
CSS_CATEGORY_ITEM = '.b-sidebar-menu__list-item'
CSS_NEWS_ITEM = '.row .js-content'
CSS_NEWS_TEXT = '.b-text p'


class LentaRuTopWordsParse:
    def __init__(self, top_words, data_dir, count_news, url=SITE_URL):
        self.top_words = top_words
        self.data_dir = data_dir
        self.count_news = count_news
        self.url = url
        self.session = HTMLSession()

    def get_category_urls(self, selector=CSS_CATEGORY_ITEM):
        resp = self.session.get(self.url)
        category_urls = []
        for el in resp.html.find(selector):
            if not el.absolute_links:
                continue
            link = el.absolute_links.pop()
            if '/rubrics/' in link:
                category_urls.append(link)
        return category_urls

    def get_news_urls(self, category_url, selector=CSS_NEWS_ITEM):
        resp = self.session.get(category_url)
        news_urls = [
            i for i in resp.html.find(selector)[0].absolute_links
            if '/news/' in i
        ]
        return news_urls[:self.count_news]

    def get_text_news(self, news_url, selector=CSS_NEWS_TEXT):
        resp = self.session.get(news_url)
        return ' '.join([i.text for i in resp.html.find(selector)])

    def get_top_category_words(self):
        for category_url in self.get_category_urls():
            print(category_url)
            for news_url in self.get_news_urls(category_url):
                print(news_url)
                print(self.get_text_news(news_url))


def save_csv(words, csv_name):
    with open(csv_name, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=('word', 'frequency'))
        writer.writeheader()
        for word, frequency in words:
            writer.writerow({'word': word, 'frequency': frequency})


def main():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Скрипт для оценки частотности слов в новостях lenta.ru"
    )
    parser.add_argument(
        '-d', '--data-dir', type=str, default='./data', required=False,
        help='Каталог для сохранения результат.'
    )
    parser.add_argument(
        '-w', '--top-words', type=int, default=20, required=False,
        help='Количество топовых слов в статьях новостей.'
    )
    parser.add_argument(
        '-n', '--count-news', type=int, default=10, required=False,
        help='Максимальное количество статьей в категории сайта, которое'
             'требуется обработать.'
    )
    args = parser.parse_args()

    parser = LentaRuTopWordsParse(
        top_words=args.top_words,
        data_dir=args.data_dir,
        count_news=args.count_news,
    )
    parser.get_top_category_words()


if __name__ == '__main__':
    main()
