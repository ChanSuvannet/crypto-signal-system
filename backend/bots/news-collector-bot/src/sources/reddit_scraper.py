# ============================================
# Crypto Trading Signal System
# backed/bots/news-collector-bot/src/sources/reddit_scraper.py
# Deception: Reddit Scraper: Uses PRAW (Python Reddit API Wrapper)
# ============================================


import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import praw


class RedditScraperSource:
    """
    Reddit scraper for crypto discussions and news
    """
    
    # Popular crypto subreddits
    CRYPTO_SUBREDDITS = [
        "CryptoCurrency",  # Main crypto sub
        "Bitcoin",  # Bitcoin discussions
        "ethereum",  # Ethereum discussions
        "CryptoMarkets",  # Trading discussions
        "altcoin",  # Altcoin discussions
        "SatoshiStreetBets",  # Crypto WSB
        "defi",  # DeFi discussions
        "NFT",  # NFT discussions
        "CryptoMoonShots",  # New projects
        "CryptoTechnology",  # Technical discussions
    ]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Reddit scraper
        
        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string
            username: Reddit username (optional)
            password: Reddit password (optional)
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=username,
                password=password
            )
            
            # Test connection
            self.reddit.user.me()
            self.logger.info("Reddit API initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {e}")
            self.reddit = None
    
    async def scrape_subreddit_posts(
        self,
        subreddit_name: str,
        sort_by: str = "hot",  # hot, new, top, rising
        time_filter: str = "day",  # hour, day, week, month, year, all
        limit: int = 100
    ) -> List[Dict]:
        """
        Scrape posts from subreddit
        
        Args:
            subreddit_name: Name of subreddit
            sort_by: Sort method
            time_filter: Time filter for 'top'
            limit: Max posts
        
        Returns:
            List of posts
        """
        if not self.reddit:
            return []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort method (run in executor)
            loop = asyncio.get_event_loop()
            
            if sort_by == "hot":
                posts = await loop.run_in_executor(
                    None,
                    lambda: list(subreddit.hot(limit=limit))
                )
            elif sort_by == "new":
                posts = await loop.run_in_executor(
                    None,
                    lambda: list(subreddit.new(limit=limit))
                )
            elif sort_by == "top":
                posts = await loop.run_in_executor(
                    None,
                    lambda: list(subreddit.top(time_filter=time_filter, limit=limit))
                )
            elif sort_by == "rising":
                posts = await loop.run_in_executor(
                    None,
                    lambda: list(subreddit.rising(limit=limit))
                )
            else:
                posts = []
            
            # Parse posts
            parsed = []
            for post in posts:
                parsed_post = self._parse_post(post, subreddit_name)
                if parsed_post:
                    parsed.append(parsed_post)
            
            self.logger.info(f"Scraped {len(parsed)} posts from r/{subreddit_name}")
            return parsed
        
        except Exception as e:
            self.logger.error(f"Error scraping r/{subreddit_name}: {e}", exc_info=True)
            return []
    
    async def scrape_all_crypto_subs(
        self,
        sort_by: str = "hot",
        posts_per_sub: int = 50
    ) -> List[Dict]:
        """
        Scrape posts from all crypto subreddits
        
        Args:
            sort_by: Sort method
            posts_per_sub: Max posts per subreddit
        
        Returns:
            List of all posts
        """
        try:
            all_posts = []
            
            for subreddit in self.CRYPTO_SUBREDDITS:
                posts = await self.scrape_subreddit_posts(
                    subreddit_name=subreddit,
                    sort_by=sort_by,
                    limit=posts_per_sub
                )
                all_posts.extend(posts)
                
                # Small delay between subreddits
                await asyncio.sleep(2)
            
            self.logger.info(f"Scraped {len(all_posts)} posts from {len(self.CRYPTO_SUBREDDITS)} subreddits")
            return all_posts
        
        except Exception as e:
            self.logger.error(f"Error scraping crypto subreddits: {e}")
            return []
    
    async def search_posts(
        self,
        query: str,
        subreddit_name: Optional[str] = None,
        time_filter: str = "day",
        limit: int = 100
    ) -> List[Dict]:
        """
        Search Reddit posts
        
        Args:
            query: Search query
            subreddit_name: Specific subreddit (None = all)
            time_filter: Time filter
            limit: Max results
        
        Returns:
            List of posts
        """
        if not self.reddit:
            return []
        
        try:
            if subreddit_name:
                subreddit = self.reddit.subreddit(subreddit_name)
            else:
                # Search all crypto subreddits
                subreddit = self.reddit.subreddit("+".join(self.CRYPTO_SUBREDDITS))
            
            # Search (run in executor)
            loop = asyncio.get_event_loop()
            posts = await loop.run_in_executor(
                None,
                lambda: list(subreddit.search(query, time_filter=time_filter, limit=limit))
            )
            
            # Parse posts
            parsed = []
            for post in posts:
                parsed_post = self._parse_post(post, subreddit_name or "multiple")
                if parsed_post:
                    parsed.append(parsed_post)
            
            self.logger.info(f"Found {len(parsed)} posts for query: {query}")
            return parsed
        
        except Exception as e:
            self.logger.error(f"Error searching posts: {e}", exc_info=True)
            return []
    
    def _parse_post(self, post, subreddit_name: str) -> Optional[Dict]:
        """
        Parse Reddit post to standardized format
        
        Args:
            post: PRAW post object
            subreddit_name: Subreddit name
        
        Returns:
            Standardized post dictionary
        """
        try:
            # Calculate engagement score
            score = post.score
            comments = post.num_comments
            upvote_ratio = post.upvote_ratio
            
            engagement = score + (comments * 2)
            
            # Calculate impact (1-10)
            if engagement > 5000:
                impact = 10
            elif engagement > 2000:
                impact = 9
            elif engagement > 1000:
                impact = 8
            elif engagement > 500:
                impact = 7
            elif engagement > 200:
                impact = 6
            else:
                impact = 5
            
            # Boost impact for high upvote ratio
            if upvote_ratio > 0.95:
                impact = min(10, impact + 1)
            
            # Extract currencies from title and text
            text_content = f"{post.title} {post.selftext}"
            currencies = self._extract_currencies(text_content)
            
            # Determine sentiment from flair and content
            sentiment = self._determine_sentiment(post)
            
            return {
                "source": "reddit",
                "post_id": post.id,
                "title": post.title,
                "content": post.selftext,
                "url": f"https://reddit.com{post.permalink}",
                "published_at": datetime.fromtimestamp(post.created_utc),
                "subreddit": subreddit_name,
                "author": str(post.author) if post.author else "[deleted]",
                "flair": post.link_flair_text,
                "engagement": {
                    "score": score,
                    "upvote_ratio": upvote_ratio,
                    "comments": comments,
                    "total": engagement,
                },
                "currencies": currencies,
                "impact": impact,
                "sentiment": sentiment,
                "is_discussion": post.is_self,
                "is_nsfw": post.over_18,
                "metadata": {
                    "awards": post.total_awards_received,
                    "distinguished": post.distinguished,
                    "stickied": post.stickied,
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing post: {e}")
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
            "BINANCE": "BNB",
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
    
    def _determine_sentiment(self, post) -> str:
        """Determine sentiment from post"""
        # Check flair
        flair = (post.link_flair_text or "").lower()
        
        if any(word in flair for word in ["bullish", "gains", "moon", "pump"]):
            return "bullish"
        elif any(word in flair for word in ["bearish", "loss", "dump", "crash"]):
            return "bearish"
        
        # Check title
        title_lower = post.title.lower()
        
        bullish_words = ["moon", "bullish", "pump", "gains", "buy", "bull run", "rocket", "🚀"]
        bearish_words = ["bearish", "dump", "crash", "bear", "sell", "loss", "down"]
        
        bullish_count = sum(1 for word in bullish_words if word in title_lower)
        bearish_count = sum(1 for word in bearish_words if word in title_lower)
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        
        return "neutral"
    
    async def get_trending_discussions(
        self,
        subreddit_name: str = "CryptoCurrency",
        hours_back: int = 24,
        min_comments: int = 50
    ) -> List[Dict]:
        """
        Get trending discussions with high engagement
        
        Args:
            subreddit_name: Subreddit to check
            hours_back: Time window
            min_comments: Minimum comments threshold
        
        Returns:
            List of trending posts
        """
        try:
            posts = await self.scrape_subreddit_posts(
                subreddit_name=subreddit_name,
                sort_by="hot",
                limit=100
            )
            
            # Filter for recent and engaging posts
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            trending = []
            for post in posts:
                pub_date = post.get("published_at")
                comments = post.get("engagement", {}).get("comments", 0)
                
                if pub_date and pub_date >= cutoff_time and comments >= min_comments:
                    trending.append(post)
            
            # Sort by engagement
            trending.sort(
                key=lambda x: x.get("engagement", {}).get("total", 0),
                reverse=True
            )
            
            return trending
        
        except Exception as e:
            self.logger.error(f"Error getting trending discussions: {e}")
            return []
    
    async def monitor_subreddit(
        self,
        subreddit_name: str,
        interval_minutes: int = 5
    ):
        """
        Monitor subreddit for new posts (streaming)
        
        Args:
            subreddit_name: Subreddit to monitor
            interval_minutes: Check interval
        """
        self.logger.info(f"Monitoring r/{subreddit_name} for new posts...")
        
        last_post_id = None
        
        while True:
            try:
                # Get latest posts
                posts = await self.scrape_subreddit_posts(
                    subreddit_name=subreddit_name,
                    sort_by="new",
                    limit=10
                )
                
                if posts:
                    latest_post = posts[0]
                    current_id = latest_post.get("post_id")
                    
                    if last_post_id and current_id != last_post_id:
                        self.logger.info(
                            f"🆕 New post in r/{subreddit_name}: "
                            f"{latest_post.get('title')[:100]}..."
                        )
                        # TODO: Send notification or trigger alert
                    
                    last_post_id = current_id
                
                # Wait before next check
                await asyncio.sleep(interval_minutes * 60)
            
            except Exception as e:
                self.logger.error(f"Error monitoring r/{subreddit_name}: {e}")
                await asyncio.sleep(60)
    
    async def close(self):
        """Cleanup resources"""
        self.logger.info("Reddit scraper closed")