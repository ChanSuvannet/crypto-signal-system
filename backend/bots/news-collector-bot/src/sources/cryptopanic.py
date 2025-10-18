# ============================================
# Crypto Trading Signal System
# backed/bots/news-collector-bot/src/sources/cryptopanic.py
# Deception: CryptoPanic News Source: Collects crypto news from CryptoPanic API
# ============================================
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from ratelimit import limits, sleep_and_retry


class CryptoPanicSource:
    """
    CryptoPanic news collector
    Free tier: 50 requests/day, public news only
    """

    BASE_URL = "https://cryptopanic.com/api/v1"

    def __init__(self, api_key: Optional[str], logger: logging.Logger):
        """
        Initialize CryptoPanic source

        Args:
            api_key: CryptoPanic API key (optional for public feed)
            logger: Logger instance
        """
        self.api_key = api_key
        self.logger = logger
        self.session: Optional[aiohttp.ClientSession] = None

        self.logger.info("CryptoPanic source initialized")

    async def connect(self):
        """Setup HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            self.logger.info("CryptoPanic HTTP session created")

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.logger.info("CryptoPanic HTTP session closed")

    @sleep_and_retry
    @limits(calls=50, period=86400)  # 50 calls per day
    async def fetch_posts(
        self,
        currencies: Optional[List[str]] = None,
        filter_type: str = "hot",  # hot, rising, bullish, bearish, important, saved, lol
        regions: Optional[str] = None,  # en, de, es, fr, nl, it, pt, ru
        kind: str = "news",  # news, media, all
        limit: int = 50,
    ) -> List[Dict]:
        """
        Fetch news posts from CryptoPanic

        Args:
            currencies: List of currency codes (BTC, ETH, etc.)
            filter_type: Type of news filter
            regions: Language/region filter
            kind: Type of content
            limit: Number of posts to fetch

        Returns:
            List of news articles
        """
        try:
            if not self.session:
                await self.connect()

            # Build request params
            params = {
                "filter": filter_type,
                "kind": kind,
            }

            # Add API key if available
            if self.api_key:
                params["auth_token"] = self.api_key
            else:
                params["public"] = "true"

            # Add currencies filter
            if currencies:
                params["currencies"] = ",".join(currencies)

            # Add region filter
            if regions:
                params["regions"] = regions

            # Make request
            url = f"{self.BASE_URL}/posts/"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])

                    # Parse and format results
                    articles = []
                    for post in results[:limit]:
                        article = self._parse_post(post)
                        if article:
                            articles.append(article)

                    self.logger.info(
                        f"Fetched {len(articles)} articles from CryptoPanic"
                    )
                    return articles

                elif response.status == 429:
                    self.logger.warning("CryptoPanic rate limit exceeded")
                    return []

                else:
                    self.logger.error(f"CryptoPanic API error: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"Error fetching CryptoPanic posts: {e}", exc_info=True)
            return []

    def _parse_post(self, post: Dict) -> Optional[Dict]:
        """
        Parse CryptoPanic post to standardized format

        Args:
            post: Raw post data from API

        Returns:
            Standardized article dictionary
        """
        try:
            # Extract currencies mentioned
            currencies = []
            for currency in post.get("currencies", []):
                currencies.append(currency.get("code", "").upper())

            # Calculate sentiment from votes
            votes = post.get("votes", {})
            positive = votes.get("positive", 0)
            negative = votes.get("negative", 0)
            important = votes.get("important", 0)
            liked = votes.get("liked", 0)
            disliked = votes.get("disliked", 0)

            total_votes = positive + negative + important + liked + disliked
            sentiment_score = 0.0

            if total_votes > 0:
                sentiment_score = (positive + liked - negative - disliked) / total_votes

            # Determine sentiment label
            if sentiment_score > 0.2:
                sentiment = "bullish"
            elif sentiment_score < -0.2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"

            # Calculate impact score (1-10)
            impact = min(10, max(1, important + (total_votes // 10)))

            return {
                "source": "cryptopanic",
                "article_id": str(post.get("id")),
                "title": post.get("title", ""),
                "url": post.get("url", ""),
                "published_at": self._parse_date(post.get("published_at")),
                "domain": post.get("domain", ""),
                "currencies": currencies,
                "kind": post.get("kind", "news"),  # news, media
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "impact": impact,
                "votes": {
                    "positive": positive,
                    "negative": negative,
                    "important": important,
                    "liked": liked,
                    "disliked": disliked,
                    "total": total_votes,
                },
                "metadata": {
                    "source_id": post.get("id"),
                    "source_created_at": post.get("created_at"),
                },
            }

        except Exception as e:
            self.logger.error(f"Error parsing CryptoPanic post: {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime"""
        if not date_str:
            return None

        try:
            # CryptoPanic uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {e}")
            return None

    async def get_trending_currencies(self) -> List[str]:
        """
        Get trending currencies

        Returns:
            List of trending currency codes
        """
        try:
            # Fetch hot news and extract most mentioned currencies
            articles = await self.fetch_posts(filter_type="hot", limit=100)

            # Count currency mentions
            currency_counts = {}
            for article in articles:
                for currency in article.get("currencies", []):
                    currency_counts[currency] = currency_counts.get(currency, 0) + 1

            # Sort by count
            trending = sorted(currency_counts.items(), key=lambda x: x[1], reverse=True)

            # Return top 10
            return [currency for currency, _ in trending[:10]]

        except Exception as e:
            self.logger.error(f"Error getting trending currencies: {e}")
            return []

    async def search_by_currency(
        self, currency: str, hours_back: int = 24, limit: int = 50
    ) -> List[Dict]:
        """
        Search news for specific currency

        Args:
            currency: Currency code (e.g., BTC, ETH)
            hours_back: How many hours back to search
            limit: Max results

        Returns:
            List of articles
        """
        try:
            articles = await self.fetch_posts(
                currencies=[currency.upper()], filter_type="hot", limit=limit
            )

            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            filtered = []
            for article in articles:
                pub_date = article.get("published_at")
                if pub_date and pub_date >= cutoff_time:
                    filtered.append(article)

            self.logger.info(
                f"Found {len(filtered)} articles for {currency} in last {hours_back}h"
            )
            return filtered

        except Exception as e:
            self.logger.error(f"Error searching currency {currency}: {e}")
            return []

    async def get_important_news(self, limit: int = 20) -> List[Dict]:
        """
        Get important/breaking news

        Args:
            limit: Max results

        Returns:
            List of important articles
        """
        try:
            articles = await self.fetch_posts(filter_type="important", limit=limit)

            # Sort by impact score
            articles.sort(key=lambda x: x.get("impact", 0), reverse=True)

            return articles

        except Exception as e:
            self.logger.error(f"Error getting important news: {e}")
            return []
