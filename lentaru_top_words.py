import argparse
import os

from datetime import datetime

from parser import LentaRuParserTopWords


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
