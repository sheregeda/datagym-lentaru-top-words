import argparse
import csv


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
        '-d', '--data-dir', type=str, default='./data', required=True,
        help='Каталог для сохранения результат.'
    )
    parser.add_argument(
        '-c', '--count-words', type=int, default=20, required=True,
        help='Количество топовых слов в статьях новостей.'
    )
    args = parser.parse_args()


if __name__ == '__main__':
    main()
