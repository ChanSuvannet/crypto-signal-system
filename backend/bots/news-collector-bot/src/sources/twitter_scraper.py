
# ============================================
# Crypto Trading Signal System
# backed/bots/news-collector-bot/src/sources/twitter_scraper.py
# Deception: Twitter/X Scraper: Uses snscrape (no API key needed) or tweepy (with API key)
# ============================================

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    import snscrape.modules.twitter as sntwitter

    SNSCRAPE_AVAILABLE = True
except ImportError:
    SNSCRAPE_AVAILABLE = False

try:
    import tweepy

    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False


class TwitterScraperSource:
    """
    Twitter/X scraper for crypto news and sentiment
    """

    # Influential crypto Twitter accounts
    CRYPTO_ACCOUNTS = [
        "VitalikButerin",  # Ethereum founder
        "cz_binance",  # Binance CEO
        "elonmusk",  # Tesla CEO (influences crypto)
        "Saylor Michael",  # MicroStrategy CEO
        "naval",  # AngelList founder
        "aantonop",  # Andreas Antonopoulos
        "APompliano",  # Anthony Pompliano
        "CryptoCobain",  # Crypto trader
        "woonomic",  # Willy Woo
        "100trillionUSD",  # PlanB
        "DocumentingBTC",  # Bitcoin documenter
        "Crypto Rover",  # Crypto news
    ]

    # Crypto keywords to search
    CRYPTO_KEYWORDS = [
        "$BTC",
        "$ETH",
        "$BNB",
        "$SOL",
        "$XRP",
        "bitcoin",
        "ethereum",
        "crypto",
        "cryptocurrency",
        "blockchain",
        "defi",
        "nft",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Twitter scraper

        Args:
            api_key: Twitter API key (optional)
            api_secret: Twitter API secret (optional)
            access_token: Twitter access token (optional)
            access_token_secret: Twitter access token secret (optional)
            bearer_token: Twitter bearer token (optional)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Try to use Tweepy if credentials provided
        self.tweepy_client = None
        if TWEEPY_AVAILABLE and bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=bearer_token)
                self.logger.info("Twitter API (Tweepy) initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Tweepy: {e}")

        # Fallback to snscrape (no API key needed)
        if not self.tweepy_client and SNSCRAPE_AVAILABLE:
            self.logger.info("Using snscrape for Twitter (no API key required)")
        elif not self.tweepy_client and not SNSCRAPE_AVAILABLE:
            self.logger.warning(
                "Neither Tweepy nor snscrape available. Install: pip install tweepy snscrape"
            )

    async def scrape_tweets(
        self,
        query: str,
        since_date: Optional[datetime] = None,
        until_date: Optional[datetime] = None,
        limit: int = 100,
        lang: str = "en",
    ) -> List[Dict]:
        """
        Scrape tweets using snscrape (no API key needed)

        Args:
            query: Search query
            since_date: Start date
            until_date: End date
            limit: Max tweets
            lang: Language filter

        Returns:
            List of tweets
        """
        if not SNSCRAPE_AVAILABLE:
            self.logger.error("snscrape not available")
            return []

        try:
            # Build query
            search_query = f"{query} lang:{lang}"

            if since_date:
                search_query += f" since:{since_date.strftime('%Y-%m-%d')}"

            if until_date:
                search_query += f" until:{until_date.strftime('%Y-%m-%d')}"

            # Scrape tweets (runs in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            tweets = await loop.run_in_executor(
                None,
                lambda: list(sntwitter.TwitterSearchScraper(search_query).get_items())[
                    :limit
                ],
            )

            # Parse tweets
            parsed = []
            for tweet in tweets:
                parsed_tweet = self._parse_tweet_snscrape(tweet)
                if parsed_tweet:
                    parsed.append(parsed_tweet)

            self.logger.info(f"Scraped {len(parsed)} tweets for query: {query}")
            return parsed

        except Exception as e:
            self.logger.error(f"Error scraping tweets: {e}", exc_info=True)
            return []

    async def scrape_user_tweets(
        self, username: str, since_date: Optional[datetime] = None, limit: int = 50
    ) -> List[Dict]:
        """
        Scrape tweets from specific user

        Args:
            username: Twitter username
            since_date: Start date
            limit: Max tweets

        Returns:
            List of tweets
        """
        if not SNSCRAPE_AVAILABLE:
            return []

        try:
            query = f"from:{username}"
            return await self.scrape_tweets(
                query=query, since_date=since_date, limit=limit
            )

        except Exception as e:
            self.logger.error(f"Error scraping user {username}: {e}")
            return []

    async def get_crypto_influencer_tweets(
        self, hours_back: int = 24, tweets_per_account: int = 10
    ) -> List[Dict]:
        """
        Get tweets from crypto influencers

        Args:
            hours_back: How many hours back
            tweets_per_account: Max tweets per account

        Returns:
            List of tweets
        """
        try:
            since_date = datetime.now() - timedelta(hours=hours_back)

            all_tweets = []

            for username in self.CRYPTO_ACCOUNTS:
                tweets = await self.scrape_user_tweets(
                    username=username, since_date=since_date, limit=tweets_per_account
                )
                all_tweets.extend(tweets)

                # Small delay to avoid rate limiting
                await asyncio.sleep(1)

            self.logger.info(
                f"Collected {len(all_tweets)} tweets from {len(self.CRYPTO_ACCOUNTS)} influencers"
            )
            return all_tweets

        except Exception as e:
            self.logger.error(f"Error getting influencer tweets: {e}")
            return []

    async def search_crypto_tweets(
        self, hours_back: int = 24, limit: int = 100
    ) -> List[Dict]:
        """
        Search tweets with crypto keywords

        Args:
            hours_back: How many hours back
            limit: Max tweets

        Returns:
            List of tweets
        """
        try:
            since_date = datetime.now() - timedelta(hours=hours_back)

            # Build query with keywords
            query = " OR ".join(self.CRYPTO_KEYWORDS[:5])  # Top 5 keywords

            tweets = await self.scrape_tweets(
                query=query, since_date=since_date, limit=limit
            )

            return tweets

        except Exception as e:
            self.logger.error(f"Error searching crypto tweets: {e}")
            return []

    def _parse_tweet_snscrape(self, tweet) -> Optional[Dict]:
        """
        Parse snscrape tweet to standardized format

        Args:
            tweet: Raw tweet from snscrape

        Returns:
            Standardized tweet dictionary
        """
        try:
            # Extract mentioned currencies
            currencies = self._extract_currencies_from_text(tweet.content)

            # Calculate impact based on engagement
            likes = tweet.likeCount or 0
            retweets = tweet.retweetCount or 0
            replies = tweet.replyCount or 0

            total_engagement = likes + (retweets * 2) + replies

            # Impact score (1-10)
            if total_engagement > 10000:
                impact = 10
            elif total_engagement > 5000:
                impact = 9
            elif total_engagement > 1000:
                impact = 8
            elif total_engagement > 500:
                impact = 7
            elif total_engagement > 100:
                impact = 6
            else:
                impact = 5

            # Check if from verified account or influencer
            is_verified = (
                tweet.user.verified if hasattr(tweet.user, "verified") else False
            )
            is_influencer = tweet.user.username in self.CRYPTO_ACCOUNTS

            if is_verified or is_influencer:
                impact = min(10, impact + 1)

            return {
                "source": "twitter",
                "tweet_id": str(tweet.id),
                "content": tweet.content,
                "url": tweet.url,
                "published_at": tweet.date,
                "author": {
                    "username": tweet.user.username,
                    "display_name": tweet.user.displayname,
                    "followers": tweet.user.followersCount,
                    "verified": is_verified,
                    "is_influencer": is_influencer,
                },
                "engagement": {
                    "likes": likes,
                    "retweets": retweets,
                    "replies": replies,
                    "total": total_engagement,
                },
                "currencies": currencies,
                "impact": impact,
                "hashtags": tweet.hashtags or [],
                "cashtags": self._extract_cashtags(tweet.content),
                "media": [media.url for media in (tweet.media or [])],
                "metadata": {
                    "tweet_type": "original" if not tweet.inReplyToTweetId else "reply",
                    "is_retweet": bool(tweet.retweetedTweet),
                },
            }

        except Exception as e:
            self.logger.error(f"Error parsing tweet: {e}")
            return None

    def _extract_currencies_from_text(self, text: str) -> List[str]:
        """Extract cryptocurrency codes from text"""
        currencies = []
        text_upper = text.upper()

        # Common crypto patterns
        crypto_map = {
            "$BTC": "BTC",
            "BITCOIN": "BTC",
            "$ETH": "ETH",
            "ETHEREUM": "ETH",
            "$BNB": "BNB",
            "$SOL": "SOL",
            "SOLANA": "SOL",
            "$XRP": "XRP",
            "$ADA": "ADA",
            "CARDANO": "ADA",
            "$DOGE": "DOGE",
            "DOGECOIN": "DOGE",
            "$MATIC": "MATIC",
            "POLYGON": "MATIC",
            "$DOT": "DOT",
            "POLKADOT": "DOT",
            "$AVAX": "AVAX",
            "AVALANCHE": "AVAX",
        }

        for pattern, code in crypto_map.items():
            if pattern in text_upper:
                if code not in currencies:
                    currencies.append(code)

        return currencies

    def _extract_cashtags(self, text: str) -> List[str]:
        """Extract cashtags ($BTC, $ETH, etc.) from text"""
        cashtag_pattern = r"\$[A-Z]{2,10}"
        cashtags = re.findall(cashtag_pattern, text.upper())
        return list(set(cashtags))

    async def get_trending_crypto_topics(self, limit: int = 20) -> List[Dict]:
        """
        Get trending crypto topics based on recent tweets

        Args:
            limit: Number of tweets to analyze

        Returns:
            List of trending topics with frequency
        """
        try:
            # Get recent crypto tweets
            tweets = await self.search_crypto_tweets(hours_back=2, limit=limit * 5)

            # Count hashtag frequencies
            hashtag_counts = {}
            cashtag_counts = {}

            for tweet in tweets:
                for hashtag in tweet.get("hashtags", []):
                    hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1

                for cashtag in tweet.get("cashtags", []):
                    cashtag_counts[cashtag] = cashtag_counts.get(cashtag, 0) + 1

            # Combine and sort
            all_topics = []

            for tag, count in hashtag_counts.items():
                all_topics.append(
                    {"topic": f"#{tag}", "type": "hashtag", "count": count}
                )

            for tag, count in cashtag_counts.items():
                all_topics.append({"topic": tag, "type": "cashtag", "count": count})

            # Sort by count
            all_topics.sort(key=lambda x: x["count"], reverse=True)

            return all_topics[:limit]

        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []

    async def monitor_influencer_activity(
        self, username: str, interval_minutes: int = 5
    ):
        """
        Monitor specific influencer for new tweets (streaming)

        Args:
            username: Twitter username to monitor
            interval_minutes: Check interval
        """
        self.logger.info(f"Monitoring {username} for new tweets...")

        last_tweet_id = None

        while True:
            try:
                # Get latest tweets
                tweets = await self.scrape_user_tweets(username=username, limit=10)

                # Check for new tweets
                if tweets:
                    latest_tweet = tweets[0]
                    current_id = latest_tweet.get("tweet_id")

                    if last_tweet_id and current_id != last_tweet_id:
                        self.logger.info(
                            f"🚨 New tweet from @{username}: {latest_tweet.get('content')[:100]}..."
                        )
                        # TODO: Send notification or trigger alert

                    last_tweet_id = current_id

                # Wait before next check
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                self.logger.error(f"Error monitoring {username}: {e}")
                await asyncio.sleep(60)

    async def close(self):
        """Cleanup resources"""
        self.logger.info("Twitter scraper closed")
