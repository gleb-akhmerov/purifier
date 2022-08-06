import copy
import dataclasses
import json as json_lib
import ssl
from base64 import b64decode
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Dict, Callable, Literal, List, Union

import cloudscraper
import jq as jq_lib
import lxml.html
from bs4 import BeautifulSoup
from jsonfinder import jsonfinder
from lxml.html import HtmlElement
import lxml.etree
import requests
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.util.ssl_ import create_urllib3_context


A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")

T = TypeVar("T")


# https://scrapfly.io/blog/how-to-avoid-web-scraping-blocking-tls/
class TlsAdapter(HTTPAdapter):
    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = create_urllib3_context(
            ciphers="ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384",
            cert_reqs=ssl.CERT_REQUIRED,
            options=self.ssl_options,
        )
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)


@dataclass(frozen=True)
class ScraperState(Generic[A]):
    url: str
    state: A

    def map(self, f: Callable[[A], B]) -> "ScraperState[B]":
        state2 = f(self.state)
        return dataclasses.replace(self, state=state2)  # type: ignore


class ScrapeError(Exception):
    pass


class Scraper(Generic[A, B]):
    def __init__(self, scrape_simple: Optional[Callable[[A], B]] = None) -> None:
        self._scrape_simple = scrape_simple

    def _scrape_impl(self, state: ScraperState[A]) -> ScraperState[B]:
        if self._scrape_simple is None:
            raise NotImplementedError
        else:
            return state.map(self._scrape_simple)

    def scrape(self, url) -> B:
        state = ScraperState(state=url, url=url)
        return self._scrape_impl(state).state

    def __or__(self, other: "Scraper[B, C]") -> "Scraper[A, C]":
        """
        a | b
        """
        return Pipe(self, other)

    def __mod__(self, other: "Scraper[B, C]") -> "Scraper[A, Optional[C]]":
        """
        a % b
        """
        return MaybePipe(self, other)

    def __floordiv__(self, other: "Scraper[A, C]") -> "Scraper[A, Union[B, C]]":
        """
        a // b
        """
        return Alternative(self, other)


@dataclass
class Pipe(Scraper[A, C], Generic[A, B, C]):
    a: Scraper[A, B]
    b: Scraper[B, C]

    def _scrape_impl(self, state: ScraperState[A]) -> ScraperState[C]:
        state2 = self.a._scrape_impl(state)
        return self.b._scrape_impl(state2)


@dataclass
class MaybePipe(Scraper[A, Optional[C]], Generic[A, B, C]):
    a: Scraper[A, B]
    b: Scraper[B, C]

    def _scrape_impl(self, state: ScraperState[A]) -> ScraperState[Optional[C]]:
        try:
            state2 = self.a._scrape_impl(state)
        except ScrapeError:
            return dataclasses.replace(state, state=None)  # type: ignore
        return self.b._scrape_impl(state2)  # type: ignore


@dataclass
class Alternative(Scraper[A, Union[B, C]], Generic[A, B, C]):
    a: Scraper[A, B]  # possibly `B = Optional[...]`
    b: Scraper[A, C]  # possibly `C = Optional[...]`

    def _scrape_impl(self, state: ScraperState[A]) -> ScraperState[Union[B, C]]:
        state2 = self.a._scrape_impl(state)
        if state2.state is not None:
            return state2  # type: ignore
        else:
            return self.b._scrape_impl(state)


@dataclass
class fields(Scraper[T, Dict[str, object]]):
    fields: Dict[str, Scraper[T, object]]

    def __init__(self, **kwargs):
        super().__init__()
        self.fields = kwargs

    def _scrape_impl(self, state: ScraperState[T]) -> ScraperState[Dict[str, object]]:
        return dataclasses.replace(
            state,  # type: ignore
            state={
                field: field_scraper._scrape_impl(state).state
                for field, field_scraper in self.fields.items()
            },
        )


@dataclass
class maps(Scraper[List[A], List[B]]):
    scraper: Scraper[A, B]

    def _scrape_impl(self, state: ScraperState[List[A]]) -> ScraperState[List[B]]:
        return dataclasses.replace(
            state,  # type: ignore
            state=[
                self.scraper._scrape_impl(dataclasses.replace(state, state=x)).state  # type: ignore
                for x in state.state
            ],
        )


def request(
    headers: Optional[dict[str, str]] = None,
    lib: Literal["requests", "cloudscraper"] = "requests",
) -> Scraper[str, str]:
    def scrape(url: str) -> str:
        session_by_lib = {
            "requests": requests.session,
            "cloudscraper": cloudscraper.create_scraper,
        }
        session = session_by_lib[lib]()

        # https://scrapfly.io/blog/how-to-avoid-web-scraping-blocking-tls/
        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)  # prioritize TLS 1.2
        session.mount("https://", adapter)

        r = session.get(url, headers=headers)
        r.raise_for_status()

        return r.text

    return Scraper(scrape)


@dataclass
class html(Scraper):
    def _scrape_impl(self, state: ScraperState[str]) -> ScraperState[HtmlElement]:
        try:
            dom = lxml.html.fromstring(state.state)
            dom.make_links_absolute(state.url)
            return dataclasses.replace(state, state=dom)
        except lxml.etree.ParserError:
            raise ScrapeError


def xpath(path: str) -> Scraper[HtmlElement, List[HtmlElement]]:
    find = lxml.etree.XPath(path)
    return Scraper(lambda dom: find(dom))


def one() -> Scraper[List[A], A]:
    def scrape(xs: list[A]) -> A:
        if len(xs) != 1:
            raise ScrapeError(f"one() found {len(xs)} matches, expected 1")
        return xs[0]

    return Scraper(scrape)


def first() -> Scraper[List[A], A]:
    def scrape(xs: list[A]) -> A:
        if len(xs) == 0:
            raise ScrapeError(f"first() found 0 matches, expected at least 1")
        return xs[0]

    return Scraper(scrape)


def json() -> Scraper[str, T]:
    return Scraper(json_lib.loads)


def base64() -> Scraper[str, bytes]:
    return Scraper(lambda b64_str: b64decode(b64_str.encode(), validate=True))


def jq(expr: str) -> Scraper[A, B]:
    return Scraper(lambda inp: jq_lib.compile(expr).input(inp).first())


def html_to_text() -> Scraper[HtmlElement, str]:
    def scrape(dom: HtmlElement) -> str:
        dom = copy.deepcopy(dom)
        # FIXME: <p>
        for br in dom.xpath("//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        return dom.text_content()

    return Scraper(scrape)


def rstrip(chars: Optional[str] = None) -> Scraper[str, str]:
    return Scraper(lambda s: s.rstrip(chars))


def find_json() -> Scraper[str, T]:
    """
    Returns first thing in a string that is parseable as json.
    """

    def scrape(s: str) -> T:
        _start, _end, jsn = next(jsonfinder(s, json_only=True))
        return jsn

    return Scraper(scrape)


def debug_dump_json() -> Scraper[T, T]:
    def scrape(jsn: T) -> T:
        print(json_lib.dumps(jsn, indent=4, ensure_ascii=False))
        return jsn

    return Scraper(scrape)


def debug_dump_html() -> Scraper[HtmlElement, HtmlElement]:
    def scrape(dom: HtmlElement) -> HtmlElement:
        string_but_ugly_html = lxml.html.tostring(dom)
        soup = BeautifulSoup(string_but_ugly_html, "lxml")
        print(soup.prettify())
        return dom

    return Scraper(scrape)


def constantly(x: B) -> Scraper[A, B]:
    """
    Ignore input and return `x`.
    """
    return Scraper(lambda _: x)
