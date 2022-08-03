import ssl
from base64 import b64decode
import copy
import dataclasses
import json
from dataclasses import dataclass
from typing import Literal, Optional

import cloudscraper
import jq
import lxml.html
import lxml.etree

import requests
from bs4 import BeautifulSoup
from jsonfinder import jsonfinder
from parsy import string, seq, regex, forward_declaration, success, generate
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from urllib3.util.ssl_ import create_urllib3_context


__all__ = ["scrape", "scrape_impl", "parse_scraper", "ScraperState"]


@dataclass
class Scraper:
    pass


@dataclass
class Pipe(Scraper):
    l: Scraper
    r: Scraper


@dataclass
class MaybePipe(Scraper):
    l: Scraper
    r: Scraper


@dataclass
class Map(Scraper):
    map_scraper: Scraper


@dataclass
class Action(Scraper):
    pass


@dataclass
class Fields(Action):
    fields: dict[str, Scraper]


@dataclass
class Base64Decode(Action):
    pass


@dataclass
class DebugDumpHtml(Action):
    pass


@dataclass
class DebugDumpJson(Action):
    pass


@dataclass
class FindJson(Action):
    pass


@dataclass
class Html(Action):
    pass


@dataclass
class HtmlToText(Action):
    pass


@dataclass
class Jq(Action):
    path: str


@dataclass
class Json(Action):
    pass


@dataclass
class RequestGet(Action):
    headers: Optional[dict[str, str]] = None
    request_lib: Literal["requests", "cloudscraper"] = "requests"


@dataclass
class Rstrip(Action):
    chars: Optional[str] = None


@dataclass
class XpathAll(Action):
    path: str


@dataclass
class XpathOne(Action):
    path: str


def parse_scraper(scraper_str: str) -> Scraper:
    whitespace = (string(" ") | string("\n")).many()
    ws = lambda x: whitespace >> x << whitespace

    trailing_comma = string(",").optional()

    identifier = regex(r"[a-z_][a-z0-9_]*")
    quoted_string = (
        (string('"') >> regex(r'[^"]').many().concat() << string('"'))
        | (string("'") >> regex(r"[^']").many().concat() << string("'"))
    ).desc("quoted string")

    string_dict_pair = seq(
        quoted_string << ws(string(":")),
        quoted_string,
    )
    string_dict = (
        string("{")
        >> ws(string_dict_pair.sep_by(ws(string(","))))
        << trailing_comma
        << whitespace
        << string("}")
    ).map(dict)

    action_name = (
        string("base64_decode")
        | string("debug_dump_html")
        | string("debug_dump_json")
        | string("find_json")
        | string("html_to_text")
        | string("html")
        | string("jq")
        | string("json")
        | string("request_get")
        | string("rstrip")
        | string("xpath_all")
        | string("xpath_one")
    )

    scraper_by_name = {
        "base64_decode": Base64Decode,
        "debug_dump_html": DebugDumpHtml,
        "debug_dump_json": DebugDumpJson,
        "find_json": FindJson,
        "html": Html,
        "html_to_text": HtmlToText,
        "jq": Jq,
        "json": Json,
        "request_get": RequestGet,
        "rstrip": Rstrip,
        "xpath_all": XpathAll,
        "xpath_one": XpathOne,
    }

    arg = quoted_string
    args = arg.sep_by(ws(string(",")), min=1) << whitespace << trailing_comma
    kwarg_of_val = lambda val: seq(
        identifier << ws(string("=")),
        val,
    )
    kwargs_of_val = lambda val: (
        (
            kwarg_of_val(val).sep_by(ws(string(",")), min=1)
            << whitespace
            << trailing_comma
        ).map(dict)
    )

    scraper = forward_declaration()

    action = (
        # only args
        seq(
            action=action_name,
            args=string("(") >> ws(args) << string(")"),
            kwargs=success({}),
        )
        # only kwargs
        | seq(
            action=action_name,
            args=success([]),
            kwargs=string("(")
            >> ws(kwargs_of_val(quoted_string | string_dict))
            << string(")"),
        )
        # or no () at all
        | seq(
            action=action_name,
            args=success([]),
            kwargs=success({}),
        )
    ).map(lambda x: scraper_by_name[x["action"]](*x["args"], **x["kwargs"]))

    fields = (
        string("fields") >> string("(") >> ws(kwargs_of_val(scraper)) << string(")")
    ).map(Fields)

    map_ = (string("map") >> string("(") >> ws(scraper) << string(")")).map(Map)

    expr = action | fields | map_

    @generate
    def sep_by_operators():
        a = yield expr
        while True:
            op = yield ws(string("|?") | string("|")) | success(None)
            if op is None:
                return a
            elif op == "|?":
                b = yield expr
                a = MaybePipe(a, b)
            elif op == "|":
                b = yield expr
                a = Pipe(a, b)

    scraper.become(ws(sep_by_operators))
    return scraper.parse(scraper_str)


@dataclass(frozen=True)
class ScraperState:
    url: str
    state: object


class ScrapeError(Exception):
    pass


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


def perform_action(s: Scraper, state: ScraperState) -> ScraperState:
    if isinstance(s, RequestGet):
        session_by_lib = {
            "requests": requests.session,
            "cloudscraper": cloudscraper.create_scraper,
        }
        session = session_by_lib[s.request_lib]()

        # https://scrapfly.io/blog/how-to-avoid-web-scraping-blocking-tls/
        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)  # prioritize TLS 1.2
        session.mount("https://", adapter)

        r = session.get(state.state, headers=s.headers)
        r.raise_for_status()

        return dataclasses.replace(state, state=r.text)
    elif isinstance(s, Html):
        try:
            html = lxml.html.fromstring(state.state)
            html.make_links_absolute(state.url)
            return dataclasses.replace(state, state=html)
        except lxml.etree.ParserError:
            raise ScrapeError
    elif isinstance(s, XpathOne):
        xs = state.state.xpath(s.path)
        if len(xs) != 1:
            raise ScrapeError(f"{s} found {len(xs)} matches, expected 1")
        return dataclasses.replace(state, state=xs[0])
    elif isinstance(s, XpathAll):
        return dataclasses.replace(state, state=state.state.xpath(s.path))
    elif isinstance(s, Json):
        return dataclasses.replace(state, state=json.loads(state.state))
    elif isinstance(s, Base64Decode):
        return dataclasses.replace(
            state, state=b64decode(state.state.encode(), validate=True)
        )
    elif isinstance(s, Jq):
        return dataclasses.replace(
            state, state=jq.compile(s.path).input(state.state).first()
        )
    elif isinstance(s, HtmlToText):
        html = copy.deepcopy(state.state)
        # FIXME: <p>
        for br in html.xpath("//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        return dataclasses.replace(state, state=html.text_content())
    elif isinstance(s, Rstrip):
        return dataclasses.replace(state, state=state.state.rstrip(s.chars))
    elif isinstance(s, FindJson):
        # returns first thing in a string that is parseable as json
        _start, _end, jsn = next(jsonfinder(state.state, json_only=True))
        return dataclasses.replace(state, state=jsn)
    elif isinstance(s, DebugDumpJson):
        print(json.dumps(state.state, indent=4, ensure_ascii=False))
        return state
    elif isinstance(s, DebugDumpHtml):
        string_but_ugly_html = lxml.html.tostring(state.state)
        soup = BeautifulSoup(string_but_ugly_html, "lxml")
        print(soup.prettify())
        return state
    else:
        raise ValueError(s)


def scrape_impl(s: Scraper, state: ScraperState, debug: bool):
    if debug:
        print(s)
        print(repr(state))
        print()

    if isinstance(s, Pipe):
        state = dataclasses.replace(state, state=scrape_impl(s.l, state, debug))
        return scrape_impl(s.r, state, debug)
    elif isinstance(s, MaybePipe):
        try:
            state = dataclasses.replace(state, state=scrape_impl(s.l, state, debug))
        except ScrapeError:
            return None
        return scrape_impl(s.r, state, debug)
    elif isinstance(s, Fields):
        return {
            field: scrape_impl(field_scraper, state, debug)
            for field, field_scraper in s.fields.items()
        }
    elif isinstance(s, Map):
        return [
            scrape_impl(s.map_scraper, dataclasses.replace(state, state=x), debug)
            for x in state.state
        ]
    elif isinstance(s, Action):
        return perform_action(s, state).state
    else:
        raise ValueError(s, state)


def scrape(s: str, url: str, debug: bool = False):
    return scrape_impl(parse_scraper(s), ScraperState(url=url, state=url), debug=debug)
