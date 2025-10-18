"""
News Sources Module
All news collection sources for the News Collector Bot
"""

from .cryptopanic import CryptoPanicSource
from .newsapi import NewsAPISource
from .reddit_scraper import RedditScraperSource
from .rss_feeds import RSSFeedSource
from .twitter_scraper import TwitterScraperSource

__all__ = [
    "CryptoPanicSource",
    "NewsAPISource",
    "TwitterScraperSource",
    "RedditScraperSource",
    "RSSFeedSource",
]
