import csv
import os

from collections import Counter
from urllib.parse import urljoin

import pytest

from parser import LentaRuParserTopWords, CSS_CATEGORY_ITEM, SITE_URL


@pytest.fixture()
def parser(count_words, data_dir, count_news):
    return LentaRuParserTopWords(
        url=SITE_URL,
        count_words=count_words,
        data_dir=data_dir,
        count_news=count_news

    )


def test_extract_categories_ok(requests_mock, parser, css_category_item):
    categories_urls = ['/rubrics/bar/world/', '/rubrics/foo/media']
    text = f"""
    <ul>
        <li class="{css_category_item}">
            <a href="/some/url/"></a>
        </li>
        <li class="{css_category_item}">
            <a href="{categories_urls[0]}"></a>
        </li>
        <li class="{css_category_item}">
            <a href="{categories_urls[1]}"></a>
        </li>
    </ul>
    """
    requests_mock.get(SITE_URL, text=text)
    assert parser.extract_categories(CSS_CATEGORY_ITEM) == {
        'world': urljoin(SITE_URL, categories_urls[0]),
        'media': urljoin(SITE_URL, categories_urls[1])
    }


def test_extract_categories_not_found(requests_mock, parser):
    text = "There is no CSS_CATEGORY_ITEM"
    requests_mock.get(SITE_URL, text=text)
    assert parser.extract_categories(CSS_CATEGORY_ITEM) == {}


def test_save_csv(parser, data_dir):
    category_name = 'world'
    counter = Counter({'foo': 10, 'bar': 20, 'baz': 15})
    parser.save_csv(category_name, counter)

    with open(os.path.join(data_dir, f'{category_name}.csv')) as f:
        assert list(csv.reader(f)) == [
            ['word', 'frequency'], ['bar', '20'], ['baz', '15'], ['foo', '10']
        ]


@pytest.mark.parametrize('counters,result', [
    ({}, {}),
    ({
        'world': Counter({'foo': 10, 'bar': 15}),
        'media': Counter({'baz': 10}),
     }, {
        'world': Counter({'foo': 10, 'bar': 15}),
        'media': Counter({'baz': 10}),
    }),
    ({
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({'bar': 10, 'fuzz': 30}),
     }, {
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({'fuzz': 30}),
     }),
    ({
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({'foo': 5, 'bar': 10}),
     }, {
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({}),
     }),
    ({
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({'foo': 10, 'baz': 10}),
     }, {
         'world': Counter({'foo': 10, 'bar': 15}),
         'media': Counter({'baz': 10}),
     }),
])
def test_exclude_counters_intersection(parser, counters, result):
    assert parser.exclude_counters_intersection(counters) == result


def test_run(
    requests_mock, parser, css_category_item, category_url, category_name,
    css_news_item, news_url, css_news_text, data_dir
):
    text = f"""
    <ul>
        <li class="{css_category_item}">
            <a href="{category_url}"></a>
        </li>
    </ul>
    """
    requests_mock.get(SITE_URL, text=text)

    text = f"""
    <div class="row">
        <div class="{css_news_item}">
            <a href="{news_url}"></a>
        </div>
    </div>
    """
    requests_mock.get(category_url, text=text)

    text = f"""
    <div class="{css_news_text}">
        <p>foo foo bar</p>
    </div>
    """
    requests_mock.get(news_url, text=text)

    parser.run()

    with open(os.path.join(data_dir, f'{category_name}.csv')) as f:
        assert list(csv.reader(f)) == [
            ['word', 'frequency'], ['foo', '2'], ['bar', '1']
        ]
