import os
from newsapi import NewsApiClient
from time import strftime
from json import dumps

COUNTRIES_LANGUAGES = {"in": "en", "us": "en", "gb": "en"}
CATEGORIES = [
    "general",
    "business",
    "health",
    "science",
    "sports",
    "technology",
    "entertainment",
]


def get_news(country, category, api):
    newsapi = NewsApiClient(api_key=api)
    top_headlines = newsapi.get_top_headlines(
        category=category,
        country=country,
        language=COUNTRIES_LANGUAGES[country],
        page_size=100,
    )

    json_string = dumps(top_headlines)

    try:
        with open(f"{country}/{category}.json", "w") as outfile:
            outfile.write(json_string)
    except Exception as e:
        os.system(f"mkdir {country}")
        with open(f"{country}/{category}.json", "w") as outfile:
            outfile.write(json_string)


def update_top_headline():
    FIRSTAPI = os.environ.get("FIRSTAPI")
    SECONDAPI = os.environ.get("SECONDAPI")
    THIRDAPI = os.environ.get("THIRDAPI")
    FOURTHAPI = os.environ.get("FOURTHAPI")
    FIFTHAPI = os.environ.get("FIFTHAPI")
    SIXTHAPI = os.environ.get("SIXTHAPI")
    SEVENTHAPI = os.environ.get("SEVENTHAPI")

    for category in CATEGORIES:
        for country in COUNTRIES_LANGUAGES:
            print(
                f"Started category:{category} country:{country} at {strftime('%X %d %B %Y')} "
            )
            if category == "general":
                get_news(country, category, FIRSTAPI)
            elif category == "business":
                get_news(country, category, SECONDAPI)
            elif category == "health":
                get_news(country, category, THIRDAPI)
            elif category == "science":
                get_news(country, category, FOURTHAPI)
            elif category == "sports":
                get_news(country, category, FIFTHAPI)
            elif category == "technology":
                get_news(country, category, SIXTHAPI)
            elif category == "entertainment":
                get_news(country, category, SEVENTHAPI)


update_top_headline()
