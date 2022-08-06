from purifier import html, xpath, maps, fields, one, constantly, jq


def test_hacker_news_python():
    with open("test_data/Hacker News.html") as f:
        html_str = f.read()

    hacker_news_scraper = (
        constantly(html_str)
        | html()
        | xpath('//a[@class="titlelink"]')
        | maps(
            fields(
                title=xpath("text()") | one(),
                url=xpath("@href") | one(),
            )
        )
        | jq(".[:3]")
    )

    scraped = hacker_news_scraper.scrape("https://news.ycombinator.com")

    assert scraped == [
        {
            "title": "Why Is the Web So Monotonous? Google",
            "url": "https://reasonablypolymorphic.com/blog/monotonous-web/index.html",
        },
        {
            "title": "Old jokes",
            "url": "https://dynomight.net/old-jokes/",
        },
        {
            "title": "Coral makes comeback on Great Barrier Reef",
            "url": "https://www.hawkesburygazette.com.au/story/7846819/coral-makes-comeback-on-great-barrier-reef/",
        },
    ]
