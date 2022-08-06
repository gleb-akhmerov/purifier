# Available scrapers


## `request(headers: Optional[dict[str, str]] = None)`

Make an HTTP request, optionally with specified `headers`.

Input: URL (`str`).

Output: response body (`str`).

Fails: if there are network problems, on HTTP error codes or when the response
body is not a `str`.


## `html()`

Parse input as HTML and output DOM object.

Input: HTML (`str`).

Output: DOM (`lxml.html.HtmlElement`).

Fails: if the input is not a valid HTML string.


## `xpath(path: str)`

Extracts HTML elements from input by [XPath](https://devhints.io/xpath)
specified in `path`.

Input: DOM (`lxml.html.HtmlElement`).

Output: found HTML elements (`List[lxml.html.HtmlElement]`).

Fails: never.


## `json()`

Parse input as JSON. Scraper version of [json.loads](https://docs.python.org/3/library/json.html#json.loads).

Input: serialized JSON (`str`).

Output: Python JSON representation as dicts, lists, strings, etc...

Fails: if the input is not a valid serialized JSON string.


## `jq(expr: str)`

Applies `expr` as a [jq expression](https://stedolan.github.io/jq/manual/) to
the input.

Input: Python JSON representation.

Output: Python JSON representation.

Fails: never.


## `one()`

Extracts the only element from a list. The list must contain exactly one
element, otherwise fails.

Input: a list (`List[T]`).

Output: the element (`T`).

Fails: if the list doesn't contain exactly one element.


## `first()`

Extracts the first element from a list. The list must be non-empty, otherwise
fails.

Input: a list (`List[T]`).

Output: the element (`T`).

Fails: if the list is empty.


## `base64()`

Parse input as Base64.

Input: Base64 string (`str`).

Output: parsed result (`str`).

Fails: if the input is not a Base64 string.


## `html_to_text()`

Converts an HTML element to readable text. The "&lt;br/&gt;" elements are
replaced with "\n" and other elements are removed, leaving only the text.

Input: HTML element (`lxml.html.HtmlElement`).

Output: text (`str`).

Fails: never.


## `rstrip(chars: Optional[str] = None)`

Scraper version of [str.rstrip](https://docs.python.org/3/library/stdtypes.html#str.rstrip).
Optionally specify `chars` to rstrip all of these characters.

Input: (`str`).

Output: (`str`).

Fails: never.


## `find_json()`

Parses the first thing in the input that can be parsed as JSON. Fails if there's
nothing parseable. Useful for scraping information from "&lt;script&gt;" tags
containing JavaScript. Uses the [jsonfinder](https://pypi.org/project/jsonfinder/)
library.

Input: a string containing JSON (`str`).

Output: Python JSON representation as dicts, lists, strings, etc...

Fails: if there's nothing parseable as JSON.


## `constantly(x)`

Ignores the input and outputs `x`.

Input: anything.

Output: `x`.

Fails: never.


## `fields(**field_spec)`

Scrapes the input with different scrapers and put the results in a
dictionary.

Example:

```python
input = {
    "title": "Web scraping with Python",
    "metadata": {
        "tags": ["python", "web scraping", "data cleaning", "html", "xpath"],
        "length_seconds": 1276,
        "author": "John Doe",
    }
}

scraper = fields(
    title=jq('.title'),
    tags=jq('.metadata.keywords'),
)

result = scraper.scrape(input)
```
```python
result == {
    "title": "Web scraping with Python",
    "tags": ["python", "web scraping", "data cleaning", "html", "xpath"]
}
```

Input: depends on the `field_spec`.

Output: the scraped results in a dictionary, according to `field_spec`.

Fails: if one of the scrapers in the `field_spec` fails.


## `maps(scraper)`

Applies the `scraper` to each element in the input. This is a scraper version of
[map](https://docs.python.org/3/library/functions.html#map).

Input: a list (`List[A]`).

Output: a transformed list (`List[B]`).

Fails: if `scraper` fails on any element from input.


## `debug_dump_html()`

A scraper which pretty-prints HTML input to stdout and then outputs the input
as-is.

Input: anything (`T`).

Output: unchanged input (`T`).

Fails: never.


## `debug_dump_json()`

JSON version of `debug_dump_html()`.

Input: anything (`T`).

Output: unchanged input (`T`).

Fails: never.