# ============================================
# Crypto Trading Signal System
# backed/bots/news-collector-bot/src/sources/rss_feeds.py
# Deception:RSS Feeds Source: Collects crypto news from RSS feeds
# ============================================

import asyncio
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import feedparser


class RSSFeedSource:
    """
    RSS feed collector for crypto news
    """

    # Popular crypto news RSS feeds
    CRYPTO_FEEDS = {
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "decrypt": "https://decrypt.co/feed",
        "theblock": "https://www.theblock.co/rss.xml",
        "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
        "cryptoslate": "https://cryptoslate.com/feed/",
        "cryptopotato": "https://cryptopotato.com/feed/",
        "newsbtc": "https://www.newsbtc.com/feed/",
        "bitcoinist": "https://bitcoinist.com/feed/",
        "ambcrypto": "https://ambcrypto.com/feed/",
        "cryptobriefing": "https://cryptobriefing.com/feed/",
        "beincrypto": "https://beincrypto.com/feed/",
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize RSS feed source

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("RSS feed source initialized")

    async def fetch_feed(self, feed_url: str, feed_name: str = "unknown") -> List[Dict]:
        """
        Fetch and parse RSS feed

        Args:
            feed_url: RSS feed URL
            feed_name: Name of feed source

        Returns:
            List of articles
        """
        try:
            # Parse feed (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, lambda: feedparser.parse(feed_url))

            # Check for errors
            if feed.bozo:
                self.logger.warning(
                    f"Feed parsing warning for {feed_name}: {feed.bozo_exception}"
                )

            # Parse entries
            articles = []
            for entry in feed.entries:
                article = self._parse_entry(entry, feed_name)
                if article:
                    articles.append(article)

            self.logger.info(f"Fetched {len(articles)} articles from {feed_name}")
            return articles

        except Exception as e:
            self.logger.error(f"Error fetching feed {feed_name}: {e}", exc_info=True)
            return []

    async def fetch_all_feeds(self, max_articles_per_feed: int = 50) -> List[Dict]:
        """
        Fetch articles from all configured RSS feeds

        Args:
            max_articles_per_feed: Max articles per feed

        Returns:
            List of all articles
        """
        try:
            all_articles = []

            for feed_name, feed_url in self.CRYPTO_FEEDS.items():
                articles = await self.fetch_feed(feed_url, feed_name)

                # Limit articles per feed
                articles = articles[:max_articles_per_feed]
                all_articles.extend(articles)

                # Small delay between feeds
                await asyncio.sleep(1)

            self.logger.info(
                f"Fetched {len(all_articles)} total articles from "
                f"{len(self.CRYPTO_FEEDS)} RSS feeds"
            )
            return all_articles

        except Exception as e:
            self.logger.error(f"Error fetching all feeds: {e}")
            return []

    def _parse_entry(self, entry, feed_name: str) -> Optional[Dict]:
        """
        Parse RSS feed entry to standardized format

        Args:
            entry: Feed entry
            feed_name: Name of feed

        Returns:
            Standardized article dictionary
        """
        try:
            # Extract title
            title = entry.get("title", "")

            # Extract link
            url = entry.get("link", "")

            # Extract description/summary
            description = entry.get("description", "") or entry.get("summary", "")

            # Extract content
            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].get("value", "")

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except:
                    pass

            # Try alternative date fields
            if not published_at:
                for date_field in ["published", "updated", "created"]:
                    if hasattr(entry, date_field):
                        try:
                            date_str = getattr(entry, date_field)
                            published_at = parsedate_to_datetime(date_str)
                            break
                        except:
                            continue

            # Extract author
            author = entry.get("author", "")

            # Extract tags/categories
            tags = []
            if hasattr(entry, "tags"):
                tags = [tag.get("term", "") for tag in entry.tags]

            # Extract currencies from title and description
            currencies = self._extract_currencies(f"{title} {description}")

            # Calculate impact based on feed reputation
            impact = self._calculate_impact(feed_name, title)

            # Determine sentiment
            sentiment = self._determine_sentiment(title, description)

            return {
                "source": "rss",
                "feed_name": feed_name,
                "article_id": url,  # Use URL as unique ID
                "title": title,
                "description": description,
                "content": content,
                "url": url,
                "published_at": published_at or datetime.now(),
                "author": author,
                "tags": tags,
                "currencies": currencies,
                "impact": impact,
                "sentiment": sentiment,
                "metadata": {
                    "feed_source": feed_name,
                },
            }

        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {e}")
            return None

    def _extract_currencies(self, text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        currencies = []
        text_upper = text.upper()

        crypto_map = {
            "BITCOIN": "BTC",
            "BTC": "BTC",
            "ETHEREUM": "ETH",
            "ETH": "ETH",
            "BINANCE COIN": "BNB",
            "BNB": "BNB",
            "CARDANO": "ADA",
            "ADA": "ADA",
            "SOLANA": "SOL",
            "SOL": "SOL",
            "XRP": "XRP",
            "RIPPLE": "XRP",
            "DOGECOIN": "DOGE",
            "DOGE": "DOGE",
            "POLKADOT": "DOT",
            "DOT": "DOT",
            "POLYGON": "MATIC",
            "MATIC": "MATIC",
            "AVALANCHE": "AVAX",
            "AVAX": "AVAX",
            "CHAINLINK": "LINK",
            "LINK": "LINK",
            "UNISWAP": "UNI",
            "UNI": "UNI",
        }

        for keyword, code in crypto_map.items():
            if keyword in text_upper:
                if code not in currencies:
                    currencies.append(code)

        return currencies

    def _calculate_impact(self, feed_name: str, title: str) -> int:
        """
        Calculate impact score based on feed reputation and title

        Args:
            feed_name: Name of RSS feed
            title: Article title

        Returns:
            Impact score (1-10)
        """
        # Base impact by feed reputation
        high_impact_feeds = ["coindesk", "cointelegraph", "theblock", "decrypt"]
        medium_impact_feeds = ["bitcoinmagazine", "cryptoslate", "newsbtc"]

        if feed_name in high_impact_feeds:
            impact = 7
        elif feed_name in medium_impact_feeds:
            impact = 6
        else:
            impact = 5

        # Boost impact for breaking news or important keywords
        title_lower = title.lower()
        high_impact_keywords = [
            "breaking",
            "sec",
            "regulation",
            "ban",
            "approval",
            "crash",
            "surge",
            "record",
            "all-time high",
            "ath",
            "hack",
            "exploit",
            "emergency",
            "critical",
        ]

        if any(keyword in title_lower for keyword in high_impact_keywords):
            impact = min(10, impact + 2)

        return impact

    def _determine_sentiment(self, title: str, description: str) -> str:
        """
        Determine sentiment from title and description

        Args:
            title: Article title
            description: Article description

        Returns:
            Sentiment: bullish, bearish, or neutral
        """
        text = f"{title} {description}".lower()

        # Bullish keywords
        bullish_keywords = [
            "surge",
            "rally",
            "gain",
            "rise",
            "up",
            "growth",
            "bullish",
            "positive",
            "optimistic",
            "adoption",
            "breakthrough",
            "success",
            "milestone",
            "record high",
            "approval",
            "green",
            "pump",
        ]

        # Bearish keywords
        bearish_keywords = [
            "crash",
            "fall",
            "drop",
            "decline",
            "down",
            "loss",
            "bearish",
            "negative",
            "pessimistic",
            "warning",
            "concern",
            "risk",
            "threat",
            "ban",
            "regulation",
            "hack",
            "exploit",
            "red",
            "dump",
        ]

        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text)

        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"

    async def get_latest_news(
        self, hours_back: int = 24, min_impact: int = 5
    ) -> List[Dict]:
        """
        Get latest news articles within time window

        Args:
            hours_back: How many hours back
            min_impact: Minimum impact score

        Returns:
            List of recent articles
        """
        try:
            # Fetch all articles
            all_articles = await self.fetch_all_feeds()

            # Filter by time and impact
            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            recent_articles = []
            for article in all_articles:
                pub_date = article.get("published_at")
                impact = article.get("impact", 0)

                if pub_date and pub_date >= cutoff_time and impact >= min_impact:
                    recent_articles.append(article)

            # Sort by published date (newest first)
            recent_articles.sort(
                key=lambda x: x.get("published_at", datetime.min), reverse=True
            )

            self.logger.info(
                f"Found {len(recent_articles)} recent articles "
                f"(last {hours_back}h, impact >={min_impact})"
            )
            return recent_articles

        except Exception as e:
            self.logger.error(f"Error getting latest news: {e}")
            return []

    async def get_breaking_news(self) -> List[Dict]:
        """
        Get breaking/high-impact news

        Returns:
            List of breaking news articles
        """
        try:
            # Get very recent news with high impact
            articles = await self.get_latest_news(hours_back=6, min_impact=8)

            # Sort by impact
            articles.sort(key=lambda x: x.get("impact", 0), reverse=True)

            return articles[:20]  # Top 20 breaking news

        except Exception as e:
            self.logger.error(f"Error getting breaking news: {e}")
            return []

    async def search_by_currency(
        self, currency: str, hours_back: int = 24, limit: int = 50
    ) -> List[Dict]:
        """
        Search news for specific currency

        Args:
            currency: Currency code (BTC, ETH, etc.)
            hours_back: Time window
            limit: Max results

        Returns:
            List of articles mentioning currency
        """
        try:
            # Get recent articles
            articles = await self.get_latest_news(hours_back=hours_back)

            # Filter by currency
            currency_articles = []
            for article in articles:
                currencies = article.get("currencies", [])
                if currency.upper() in currencies:
                    currency_articles.append(article)

            # Sort by published date
            currency_articles.sort(
                key=lambda x: x.get("published_at", datetime.min), reverse=True
            )

            self.logger.info(f"Found {len(currency_articles)} articles for {currency}")
            return currency_articles[:limit]

        except Exception as e:
            self.logger.error(f"Error searching currency {currency}: {e}")
            return []

    async def get_trending_topics(self, limit: int = 20) -> List[Dict]:
        """
        Get trending topics from recent news

        Args:
            limit: Number of topics to return

        Returns:
            List of trending topics with frequency
        """
        try:
            # Get recent articles
            articles = await self.get_latest_news(hours_back=24)

            # Count currency mentions
            currency_counts = {}
            tag_counts = {}

            for article in articles:
                # Count currencies
                for currency in article.get("currencies", []):
                    currency_counts[currency] = currency_counts.get(currency, 0) + 1

                # Count tags
                for tag in article.get("tags", []):
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Combine topics
            all_topics = []

            for currency, count in currency_counts.items():
                all_topics.append(
                    {"topic": currency, "type": "currency", "count": count}
                )

            for tag, count in tag_counts.items():
                all_topics.append({"topic": tag, "type": "tag", "count": count})

            # Sort by count
            all_topics.sort(key=lambda x: x["count"], reverse=True)

            return all_topics[:limit]

        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []

    async def monitor_feeds(self, interval_minutes: int = 15):
        """
        Monitor RSS feeds for new articles (continuous)

        Args:
            interval_minutes: Check interval
        """
        self.logger.info(
            f"Starting RSS feed monitoring (check every {interval_minutes}min)..."
        )

        last_article_urls = set()

        while True:
            try:
                # Fetch all feeds
                articles = await self.fetch_all_feeds(max_articles_per_feed=10)

                # Check for new articles
                new_articles = []
                for article in articles:
                    url = article.get("article_id")
                    if url and url not in last_article_urls:
                        new_articles.append(article)
                        last_article_urls.add(url)

                if new_articles:
                    self.logger.info(f"🆕 Found {len(new_articles)} new articles")

                    # Log high-impact news
                    for article in new_articles:
                        if article.get("impact", 0) >= 8:
                            self.logger.info(
                                f"🚨 HIGH IMPACT: {article.get('title')} "
                                f"(Impact: {article.get('impact')})"
                            )

                # Clean up old URLs (keep last 1000)
                if len(last_article_urls) > 1000:
                    last_article_urls = set(list(last_article_urls)[-1000:])

                # Wait before next check
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                self.logger.error(f"Error in RSS monitoring: {e}")
                await asyncio.sleep(60)

    async def close(self):
        """Cleanup resources"""
        self.logger.info("RSS feed source closed")
