from urllib.parse import urljoin

import pytest

from lentaru_top_words import (
    LentaRuTopWordsParse, SITE_URL, CSS_CATEGORY_ITEM
)


@pytest.fixture()
def parser():
    return LentaRuTopWordsParse(top_words=20, data_dir='./data')


@pytest.fixture()
def css_category_item():
    return CSS_CATEGORY_ITEM.replace('.', '')


def test_get_category_urls_css_not_found(requests_mock, parser):
    requests_mock.get(SITE_URL, text='<p>There is not CSS_CATEGORY_LIST</p>')
    assert parser.get_category_urls() == []


def test_get_category_urls_no_links(requests_mock, parser, css_category_item):
    requests_mock.get(SITE_URL, text=f'<ul class="{css_category_item}"></ul>')
    assert parser.get_category_urls() == []


def test_get_category_urls_ok(requests_mock, parser, css_category_item):
    urls = [
        urljoin(SITE_URL, '/rubrics/russia/'),
        urljoin(SITE_URL, '/rubrics/world/'),
        urljoin(SITE_URL, '/rubrics/media/'),
    ]
    text_urls = ''.join(
        f'<li><a class="{css_category_item}" href="{i}"></li>' for i in urls
    )
    text = f'<ul>{text_urls}</ul>'

    requests_mock.get(SITE_URL, text=text)
    assert sorted(parser.get_category_urls()) == sorted(urls)
