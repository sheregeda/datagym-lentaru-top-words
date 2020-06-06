import pytest

from requests_html import HTMLSession

from parser import CSS_CATEGORY_ITEM, CSS_NEWS_ITEM, CSS_NEWS_TEXT


@pytest.fixture()
def css_category_item():
    return CSS_CATEGORY_ITEM.replace('.', '')


@pytest.fixture()
def css_news_item():
    return CSS_NEWS_ITEM.replace('.', '')


@pytest.fixture()
def css_news_text():
    return CSS_NEWS_TEXT.replace('.', '')


@pytest.fixture()
def category_url():
    return 'https://lenta.ru/rubrics/world/'


@pytest.fixture()
def category_name():
    return 'world'


@pytest.fixture()
def news_url():
    return 'https://lenta.ru/news/2018/09/15/bestplaces/'


@pytest.fixture()
def session():
    return HTMLSession()


@pytest.fixture()
def count_words():
    return 3


@pytest.fixture()
def count_news():
    return 2


@pytest.fixture()
def data_dir(tmp_path):
    return tmp_path
