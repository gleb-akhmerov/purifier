from purifier import scrape_impl, parse_scraper, ScraperState


def test_hacker_python():
    with open("test_data/Hacker News.html") as f:
        html_str = f.read()

    hacker_news_scraper = """
        html
        | xpath_all('//a[@class="titlelink"]')
        | map(
            fields(
                title = xpath_one("text()"),
                url = xpath_one("@href"),
            )
        )
    """

    scraped = scrape_impl(
        parse_scraper(hacker_news_scraper),
        state=ScraperState(url="https://news.ycombinator.com", state=html_str),
        debug=False,
    )

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
        {
            "title": "The OG Social Network: Other People’s Websites",
            "url": "https://blog.jim-nielsen.com/2022/other-peoples-websites/",
        },
        {
            "title": "Tell HN: I interviewed my dad before he died",
            "url": "https://news.ycombinator.com/item?id=32349006",
        },
        {
            "title": "Using grape harvest dates to estimate summer temperature over 650 years",
            "url": "https://tamino.wordpress.com/2022/08/02/french-heat/",
        },
        {
            "title": "C99 doesn't need function bodies, or 'VLAs are Turing complete'",
            "url": "https://lemon.rip/w/c99-vla-tricks/",
        },
        {
            "title": "How to Use an iPad as a Secure Calling and Messaging Device (Updated 2022)",
            "url": "https://yawnbox.com/blog/how-to-use-an-ipad-as-a-secure-calling-and-messaging-device/",
        },
        {
            "title": "Connect-Web: It's time for Protobuf/gRPC to be your first choice in the browser",
            "url": "https://buf.build/blog/connect-web-protobuf-grpc-in-the-browser",
        },
        {
            "title": "Software engineering books to read and reread",
            "url": "https://quentin.delcourt.be/blog/software-engineering-books-to-read-and-reread/index.html",
        },
        {
            "title": "Launch HN: CodeCrafters (YC S22) – Practice writing complex software",
            "url": "https://codecrafters.io",
        },
        {
            "title": "Excel Never Dies",
            "url": "https://www.notboring.co/p/excel-never-dies",
        },
        {
            "title": "Black holes finally proven mathematically stable",
            "url": "https://www.quantamagazine.org/black-holes-finally-proven-mathematically-stable-20220804/",
        },
        {
            "title": "Is DALL-E 2 ‘gluing things together’ without understanding their relationships?",
            "url": "https://www.unite.ai/is-dall-e-2-just-gluing-things-together-without-understanding-their-relationships/",
        },
        {
            "title": "Implementing a “mini-LaTeX” in ~2000 lines of code",
            "url": "https://nibblestew.blogspot.com/2022/07/implementing-mini-latex-in-2000-lines.html",
        },
        {
            "title": "Quaise Energy is working to create geothermal wells",
            "url": "https://news.mit.edu/2022/quaise-energy-geothermal-0628",
        },
        {
            "title": "TaxProper (YC S19) Is Hiring",
            "url": "https://taxproper.notion.site/TaxProper-is-Hiring-c38437f2d0404380a6c5c9dd790c7624",
        },
        {
            "title": "Art of README (2020)",
            "url": "https://github.com/hackergrrl/art-of-readme",
        },
        {
            "title": "Anime retailer Right Stuf has been acquired by Sony/Aniplex",
            "url": "https://www.rightstufanime.com/post/right-stuf-has-joined-the-crunchyroll-family",
        },
        {
            "title": "Solein – Protein out of thin air",
            "url": "https://www.solein.com",
        },
        {
            "title": "Apple is building a demand-side platform",
            "url": "https://digiday.com/media/apple-is-building-a-demand-side-platform/",
        },
        {
            "title": "Gaudi: A Neural Architect for Immersive 3D Scene Generation",
            "url": "https://github.com/apple/ml-gaudi",
        },
        {
            "title": "Google’s video chat merger begins: Now there are two “Google Meet” apps",
            "url": "https://arstechnica.com/gadgets/2022/08/googles-video-chat-merger-begins-now-there-are-two-google-meet-apps/",
        },
        {
            "title": "Show HN: Penumbra, a perceptually optimized color palette based on natural light",
            "url": "https://github.com/nealmckee/penumbra",
        },
        {
            "title": "A complex of Native American rock mounds bears witness to ancient traditions",
            "url": "https://www.archaeology.org/issues/476-2207/letter-from/10625-georgia-stone-mounds",
        },
        {
            "title": "Allegorical Maps of Love, Courtship, and Matrimony",
            "url": "https://publicdomainreview.org/collection/allegorical-maps-of-love-courtship-and-matrimony/",
        },
        {
            "title": "Cumulative loneliness and subsequent memory function",
            "url": "https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.12734",
        },
        {
            "title": "Strict-serializability, but at what cost, for what purpose?",
            "url": "http://muratbuffalo.blogspot.com/2022/08/strict-serializability-but-at-what-cost.html",
        },
        {
            "title": "LocalStack and AWS Parity Explained",
            "url": "https://localstack.cloud/blog/2022-08-04-parity-explained/",
        },
        {
            "title": "Hyundai rolls out 27 heavy-duty hydrogen trucks in Germany",
            "url": "https://thedriven.io/2022/08/04/hyundai-rolls-out-27-heavy-duty-hydrogen-trucks-in-germany/",
        },
    ]
