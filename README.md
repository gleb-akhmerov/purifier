# Purifier

A simple scraping library.

It allows you to easily create simple and concise scrapers, even when the input
is quite messy.


## Example usage

Extract titles and URLs of articles from Hacker News:

```python
from purifier import request, html, xpath, maps, fields, one

scraper = (
    request()
    | html()
    | xpath('//a[@class="titlelink"]')
    | maps(
        fields(
            title=xpath("text()") | one(),
            url=xpath("@href") | one(),
        )
    )
)

result = scraper.scrape("https://news.ycombinator.com")
```
```python
result == [
     {
         "title": "Why Is the Web So Monotonous? Google",
         "url": "https://reasonablypolymorphic.com/blog/monotonous-web/index.html",
     },
     {
         "title": "Old jokes",
         "url": "https://dynomight.net/old-jokes/",
     },
     ...
]
```


## Tutorial

The simplest possible scraper consists of a single action:

```python
scraper = request()
```
```python
result == (
    '<html lang="en" op="news"><head><meta name="referrer" content="origin">...'
)
```

As you can see, this scraper returns the HTTP response as a string. To do
something useful with it, connect it to another scraper:

```python
scraper = request() | html()
```
```python
result == <Element html at 0x7f1be2193e00>
```

`|` ("pipe") takes output of one action and passes it to the next one. The
`html` action parses the HTML, so you can then query it with `xpath`:

```python
scraper = (
    request()
    | html()
    | xpath('//a[@class="titlelink"]/text()')
)
```
```python
result == [
    "C99 doesn't need function bodies, or 'VLAs are Turing complete'",
    "Quaise Energy is working to create geothermal wells",
    ...
]
```

Alternatively, instead of using "/text()" at the end of the XPath, you could use
`maps` with `xpath` and `one`:

```python
scraper = (
    request()
    | html()
    | xpath('//a[@class="titlelink"]')
    | maps(xpath('text()') | one())
)
```
```python
result == [
    "Why Is the Web So Monotonous? Google",
    "Old jokes",
    ...
]
```

`maps` ("map scraper") applies a scraper to each element of its input, which can
be really powerful at times. For example, combine it with `fields`, and the
result will look a bit different:

```python
scraper = (
    request()
    | html()
    | xpath('//a[@class="titlelink"]')
    | maps(
        fields(title=xpath('text()') | one())
    )
)
```
```python
result == [
    {"title": "Why Is the Web So Monotonous? Google"},
    {"title": "Old jokes"},
    ...
]
```

`fields` constructs a dictionary, allowing you to name things and also to
extract multiple different things from a single input:

```python
scraper = (
    request()
    | html()
    | xpath('//a[@class="titlelink"]')
    | maps(
        fields(
            title=xpath('text()') | one(),
            url=xpath('@href') | one(),
        )
    )
)
```
```python
result == [
     {
         "title": "Why Is the Web So Monotonous? Google",
         "url": "https://reasonablypolymorphic.com/blog/monotonous-web/index.html",
     },
     {
         "title": "Old jokes",
         "url": "https://dynomight.net/old-jokes/",
     },
     ...
]
```