# ============================================
# Crypto Trading Signal System
# backed/bots/news-collector-bot/src/sources/newsapi.py
# Deception: NewsAPI Source: Collects general crypto news from NewsAPI.org https://newsapi.org/
# ============================================

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from newsapi import NewsApiClient


class NewsAPISource:
    """
    NewsAPI.org news collector
    Free tier: 100 requests/day, 1 month history
    """

    # Crypto-related keywords
    CRYPTO_KEYWORDS = [
        "bitcoin",
        "ethereum",
        "cryptocurrency",
        "crypto",
        "blockchain",
        "BTC",
        "ETH",
        "altcoin",
        "defi",
        "nft",
        "web3",
        "binance",
        "coinbase",
    ]

    # Crypto-related domains
    CRYPTO_SOURCES = [
        "coindesk.com",
        "cointelegraph.com",
        "decrypt.co",
        "theblock.co",
        "bitcoinmagazine.com",
        "cryptoslate.com",
        "cryptopotato.com",
        "ambcrypto.com",
        "u.today",
    ]

    def __init__(self, api_key: str, logger: logging.Logger):
        """
        Initialize NewsAPI source

        Args:
            api_key: NewsAPI.org API key
            logger: Logger instance
        """
        self.api_key = api_key
        self.logger = logger

        try:
            self.client = NewsApiClient(api_key=api_key)
            self.logger.info("NewsAPI source initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize NewsAPI: {e}")
            self.client = None

    async def fetch_everything(
        self,
        query: Optional[str] = None,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        language: str = "en",
        sort_by: str = "publishedAt",  # relevancy, popularity, publishedAt
        page_size: int = 100,
    ) -> List[Dict]:
        """
        Search all articles matching criteria

        Args:
            query: Search query
            sources: Comma-separated source IDs
            domains: Comma-separated domains
            from_date: Start date
            to_date: End date
            language: Language code
            sort_by: Sort order
            page_size: Results per page

        Returns:
            List of articles
        """
        if not self.client:
            self.logger.error("NewsAPI client not initialized")
            return []

        try:
            # Use default crypto query if none provided
            if not query and not sources and not domains:
                query = " OR ".join(self.CRYPTO_KEYWORDS[:5])  # Use top 5 keywords

            # Format dates
            from_param = from_date.strftime("%Y-%m-%d") if from_date else None
            to_param = to_date.strftime("%Y-%m-%d") if to_date else None

            # Make request (sync API, run in executor)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_everything(
                    q=query,
                    sources=sources,
                    domains=domains,
                    from_param=from_param,
                    to_param=to_param,
                    language=language,
                    sort_by=sort_by,
                    page_size=page_size,
                ),
            )

            if response.get("status") == "ok":
                articles = response.get("articles", [])

                # Parse articles
                parsed = []
                for article in articles:
                    if parsed_article := self._parse_article(article):
                        parsed.append(parsed_article)

                self.logger.info(f"Fetched {len(parsed)} articles from NewsAPI")
                return parsed

            else:
                self.logger.error(f"NewsAPI error: {response.get('message')}")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching from NewsAPI: {e}", exc_info=True)
            return []

    async def fetch_top_headlines(
        self,
        country: Optional[str] = None,
        category: Optional[str] = None,
        sources: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
    ) -> List[Dict]:
        """
        Get top headlines

        Args:
            country: Country code (us, gb, etc.)
            category: Category (business, technology, etc.)
            sources: Comma-separated source IDs
            query: Search query
            page_size: Results per page

        Returns:
            List of articles
        """
        if not self.client:
            return []

        try:
            # Default to crypto query
            if not query:
                query = "cryptocurrency OR bitcoin OR ethereum"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_top_headlines(
                    q=query,
                    country=country,
                    category=category,
                    sources=sources,
                    page_size=page_size,
                ),
            )

            if response.get("status") == "ok":
                articles = response.get("articles", [])

                parsed = []
                for article in articles:
                    if parsed_article := self._parse_article(article):
                        parsed.append(parsed_article)

                self.logger.info(f"Fetched {len(parsed)} top headlines from NewsAPI")
                return parsed

            else:
                self.logger.error(f"NewsAPI error: {response.get('message')}")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching headlines: {e}", exc_info=True)
            return []

    def _parse_article(self, article: Dict) -> Optional[Dict]:
        """
        Parse NewsAPI article to standardized format

        Args:
            article: Raw article from API

        Returns:
            Standardized article dictionary
        """
        try:
            # Extract source info
            source = article.get("source", {})
            source_name = source.get("name", "Unknown")
            source_id = source.get("id")

            # Parse published date
            published_at = None
            if article.get("publishedAt"):
                with contextlib.suppress(Exception):
                    published_at = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
            # Extract currencies mentioned in title/description
            currencies = self._extract_currencies(
                article.get("title", "") + " " + article.get("description", "")
            )

            # Calculate basic impact score
            impact = 5  # Default medium impact

            # Increase impact if from known crypto source
            if any(domain in article.get("url", "") for domain in self.CRYPTO_SOURCES):
                impact += 2

            # Increase impact if mentions major coins
            if any(coin in currencies for coin in ["BTC", "ETH"]):
                impact += 1

            impact = min(10, impact)

            return {
                "source": "newsapi",
                "article_id": article.get("url", ""),  # Use URL as ID
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage"),
                "published_at": published_at,
                "author": article.get("author"),
                "source_name": source_name,
                "source_id": source_id,
                "currencies": currencies,
                "impact": impact,
                "metadata": {"raw_source": source},
            }

        except Exception as e:
            self.logger.error(f"Error parsing NewsAPI article: {e}")
            return None

    def _extract_currencies(self, text: str) -> List[str]:
        """
        Extract cryptocurrency mentions from text

        Args:
            text: Article text

        Returns:
            List of currency codes
        """
        currencies = []
        text_upper = text.upper()

        # Common crypto mappings
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
        }

        for keyword, code in crypto_map.items():
            if keyword in text_upper:
                if code not in currencies:
                    currencies.append(code)

        return currencies

    async def get_crypto_news(
        self, hours_back: int = 24, limit: int = 100
    ) -> List[Dict]:
        """
        Get recent crypto news

        Args:
            hours_back: How many hours back
            limit: Max results

        Returns:
            List of articles
        """
        try:
            from_date = datetime.now() - timedelta(hours=hours_back)

            articles = await self.fetch_everything(
                query=" OR ".join(self.CRYPTO_KEYWORDS),
                from_date=from_date,
                language="en",
                sort_by="publishedAt",
                page_size=limit,
            )

            return articles

        except Exception as e:
            self.logger.error(f"Error getting crypto news: {e}")
            return []

    async def get_breaking_news(self) -> List[Dict]:
        """
        Get breaking crypto news (top headlines)

        Returns:
            List of breaking news articles
        """
        try:
            articles = await self.fetch_top_headlines(
                query="cryptocurrency OR bitcoin", page_size=50
            )

            # Filter for high impact only
            breaking = [
                article for article in articles if article.get("impact", 0) >= 7
            ]

            return breaking

        except Exception as e:
            self.logger.error(f"Error getting breaking news: {e}")
            return []
