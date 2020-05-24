import argparse
import csv

from requests_html import HTMLSession


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
        '-c', '--count-words', type=int, default=20, required=False,
        help='Количество топовых слов в статьях новостей.'
    )
    args = parser.parse_args()

    session = HTMLSession()
    r = session.get('https://lenta.ru/')
    cat_links = []

    for el in r.html.find('.b-sidebar-menu__list-item'):
        link = el.absolute_links.pop()
        if '/rubrics/' in link:
            cat_links.append(link)
    print(cat_links)

    r = session.get('https://lenta.ru/rubrics/world/')
    news_links = [
        i for i in r.html.find('.row .js-content')[0].absolute_links
        if '/news/' in i
    ]
    print(news_links)

    r = session.get('https://lenta.ru/news/2020/05/22/nato_uslovia/')
    text = [i.text for i in r.html.find('.b-text p')]
    print(text)


if __name__ == '__main__':
    main()
