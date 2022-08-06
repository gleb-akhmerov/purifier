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


## Installation

```
pip install purifier
```


## Docs

- [Tutorial](https://github.com/gleb-akhmerov/purifier/blob/main/docs/Tutorial.md)
- [Available scrapers](https://github.com/gleb-akhmerov/purifier/blob/main/docs/Available-scrapers.md) — API reference.
