from collections import Counter
from urllib.parse import urljoin

import pytest

from parser import LentaRuParserCategory, SITE_URL


@pytest.fixture()
def parser(category_url, session, count_news):
    return LentaRuParserCategory(
        url=category_url, session=session, count_news=count_news
    )


def test_extract_news_urls_ok(
    requests_mock, parser, css_news_item, category_url, count_news
):
    news_urls = ['/news/bar/', '/news/foo/', '/news/baz/']
    text = f"""
    <div class="row">
        <div class="{css_news_item}">
            <a href="/some/url/"></a>
            <a href="{news_urls[0]}"></a>
            <a href="{news_urls[1]}"></a>
            <a href="{news_urls[2]}"></a>
        </div>
    </div>
    """
    requests_mock.get(category_url, text=text)
    result = parser.extract_news_urls(category_url)
    assert len(result) == count_news
    assert sorted(result) == sorted(
        [urljoin(SITE_URL, i) for i in news_urls]
    )[:count_news]


def test_extract_news_urls_not_found(requests_mock, parser, category_url):
    text = '<div class="row">There is no CSS_NEWS_ITEM</div>'
    requests_mock.get(category_url, text=text)
    assert parser.extract_news_urls(category_url) == []


def test_extract_text_news_ok(requests_mock, parser, css_news_text, news_url):
    text = f"""
    <div class="{css_news_text}">
        <p>some</p>
        <p>text</p>
        <div><span>some block</span></div>
    </div>
    """
    requests_mock.get(news_url, text=text)
    assert parser.extract_text_news(news_url) == 'some text'


def test_extract_text_news_not_found(requests_mock, parser, news_url):
    text = '<div class="text">There is no CSS_NEWS_TEXT</div>'
    requests_mock.get(news_url, text=text)
    assert parser.extract_text_news(news_url) == ''


@pytest.mark.parametrize('text,result', [
    ('РеГистР', ['регистр']),
    ('451° по Фаренгейту', ['фаренгейт']),
    ('и на в слово', ['слово']),
    ('несколько слов в тексте!', ['несколько', 'слово', 'текст']),
    ('пунктуация: , ! ... — «Лето»', ['пунктуация', 'лето']),
    ('цифры 146 42 17', ['цифра']),
])
def test_preprocess_text(parser, text, result):
    assert parser.preprocess_text(text) == result


def test_get_words(
    requests_mock, parser, category_url, css_news_item, css_news_text
):
    news_urls = ['/news/bar', '/news/baz']
    category_page = f"""
    <div class="row">
        <div class="{css_news_item}">
            <a href="{news_urls[0]}"></a>
            <a href="{news_urls[1]}"></a>
        </div>
    </div>
    """
    requests_mock.get(category_url, text=category_page)

    news_page = f"""
    <div class="{css_news_text}">
        <p>one</p>
        <p>two two</p>
        <p>three three three</p>
    </div>
    """
    for url in news_urls:
        requests_mock.get(urljoin(SITE_URL, url), text=news_page)

    result = parser.get_words()
    assert result == Counter({'one': 2, 'two': 4, 'three': 6})
