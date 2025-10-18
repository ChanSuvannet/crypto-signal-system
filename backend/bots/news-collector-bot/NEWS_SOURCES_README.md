# 🗞️ News Collector Bot - Sources Module

Complete implementation of all news sources for collecting crypto news and sentiment.

---

## 📦 **Available Sources**

### **1. CryptoPanic** (`cryptopanic.py`)
- **API**: CryptoPanic News API
- **Free Tier**: 50 requests/day
- **Features**:
  - ✅ Crypto-specific news aggregation
  - ✅ Sentiment voting (bullish/bearish)
  - ✅ Impact scoring
  - ✅ Currency filtering
  - ✅ Multi-language support
  - ✅ Trending currencies detection

**Usage:**
```python
from sources.cryptopanic import CryptoPanicSource

source = CryptoPanicSource(api_key="your_api_key", logger=logger)
await source.connect()

# Get hot news
articles = await source.fetch_posts(filter_type="hot", limit=50)

# Search by currency
btc_news = await source.search_by_currency("BTC", hours_back=24)

# Get important news
breaking = await source.get_important_news(limit=20)

await source.close()
```

**API Key**: Get free key at https://cryptopanic.com/developers/api/

---

### **2. NewsAPI** (`newsapi.py`)
- **API**: NewsAPI.org
- **Free Tier**: 100 requests/day, 1 month history
- **Features**:
  - ✅ General crypto news from 50,000+ sources
  - ✅ Top headlines
  - ✅ Everything search
  - ✅ Currency extraction
  - ✅ Sentiment analysis
  - ✅ Impact scoring

**Usage:**
```python
from sources.newsapi import NewsAPISource

source = NewsAPISource(api_key="your_api_key", logger=logger)

# Get crypto news
crypto_news = await source.get_crypto_news(hours_back=24, limit=100)

# Get top headlines
headlines = await source.fetch_top_headlines(query="bitcoin", page_size=50)

# Get breaking news (high impact only)
breaking = await source.get_breaking_news()
```

**API Key**: Get free key at https://newsapi.org/

---

### **3. Twitter/X Scraper** (`twitter_scraper.py`)
- **Methods**: snscrape (no API key) or Tweepy (with API key)
- **Free Tier**: Unlimited with snscrape
- **Features**:
  - ✅ Scrape crypto tweets without API key
  - ✅ Monitor crypto influencers
  - ✅ Engagement metrics
  - ✅ Cashtag extraction ($BTC, $ETH)
  - ✅ Sentiment detection
  - ✅ Trending topics analysis

**Usage:**
```python
from sources.twitter_scraper import TwitterScraperSource

# Without API key (using snscrape)
source = TwitterScraperSource(logger=logger)

# Search tweets
tweets = await source.search_crypto_tweets(hours_back=24, limit=100)

# Get influencer tweets
influencer_tweets = await source.get_crypto_influencer_tweets(hours_back=24)

# Get trending topics
trending = await source.get_trending_crypto_topics(limit=20)

# Monitor specific user
await source.monitor_influencer_activity("VitalikButerin", interval_minutes=5)
```

**Monitored Influencers:**
- VitalikButerin (Ethereum founder)
- cz_binance (Binance CEO)
- elonmusk (Tesla CEO)
- aantonop (Andreas Antonopoulos)
- And 8 more...

---

### **4. Reddit Scraper** (`reddit_scraper.py`)
- **API**: Reddit API (PRAW)
- **Free Tier**: Generous rate limits
- **Features**:
  - ✅ Scrape crypto subreddits
  - ✅ Search discussions
  - ✅ Engagement metrics (upvotes, comments)
  - ✅ Sentiment from flairs
  - ✅ Trending discussions
  - ✅ Real-time monitoring

**Usage:**
```python
from sources.reddit_scraper import RedditScraperSource

source = RedditScraperSource(
    client_id="your_client_id",
    client_secret="your_client_secret",
    user_agent="YourApp/1.0"
)

# Scrape all crypto subreddits
posts = await source.scrape_all_crypto_subs(sort_by="hot", posts_per_sub=50)

# Search for topic
btc_posts = await source.search_posts(query="Bitcoin", time_filter="day")

# Get trending discussions
trending = await source.get_trending_discussions(
    subreddit_name="CryptoCurrency",
    hours_back=24,
    min_comments=50
)

# Monitor subreddit
await source.monitor_subreddit("CryptoCurrency", interval_minutes=5)
```

**Monitored Subreddits:**
- r/CryptoCurrency (main crypto sub)
- r/Bitcoin
- r/ethereum
- r/CryptoMarkets
- And 6 more...

**API Setup**: Create Reddit app at https://www.reddit.com/prefs/apps

---

### **5. RSS Feeds** (`rss_feeds.py`)
- **Method**: RSS/Atom feed parsing
- **Free Tier**: Unlimited
- **Features**:
  - ✅ 12 major crypto news sites
  - ✅ No API key required
  - ✅ Real-time updates
  - ✅ Impact scoring by source
  - ✅ Sentiment analysis
  - ✅ Trending topics

**Usage:**
```python
from sources.rss_feeds import RSSFeedSource

source = RSSFeedSource(logger=logger)

# Fetch all feeds
all_news = await source.fetch_all_feeds(max_articles_per_feed=50)

# Get latest news
recent = await source.get_latest_news(hours_back=24, min_impact=5)

# Get breaking news (high impact)
breaking = await source.get_breaking_news()

# Search by currency
btc_news = await source.search_by_currency("BTC", hours_back=24)

# Get trending topics
trending = await source.get_trending_topics(limit=20)

# Monitor feeds continuously
await source.monitor_feeds(interval_minutes=15)
```

**RSS Feeds:**
- CoinDesk
- Cointelegraph
- Decrypt
- TheBlock
- Bitcoin Magazine
- CryptoSlate
- And 6 more...

---

## 🔧 **Installation**

```bash
cd backend/bots/news-collector-bot
pip install -r requirements.txt
```

---

## 🔑 **API Keys Setup**

### **Required Keys:**
1. **CryptoPanic** (optional but recommended)
   - Sign up: https://cryptopanic.com/developers/api/
   - Free: 50 requests/day

2. **NewsAPI** (optional but recommended)
   - Sign up: https://newsapi.org/
   - Free: 100 requests/day

3. **Reddit API** (optional)
   - Create app: https://www.reddit.com/prefs/apps
   - Free: generous limits

4. **Twitter API** (optional)
   - Scraping works without API key
   - For API: https://developer.twitter.com/

### **Environment Variables:**

Create `secrets/api-keys.txt`:
```env
# CryptoPanic
CRYPTOPANIC_API_KEY=your_key_here

# NewsAPI
NEWSAPI_KEY=your_key_here

# Reddit
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=YourApp/1.0

# Twitter (optional)
TWITTER_BEARER_TOKEN=your_token_here
```

---

## 📊 **Data Format**

All sources return standardized article format:

```python
{
    "source": "cryptopanic",  # Source name
    "article_id": "12345",    # Unique ID
    "title": "Bitcoin surges...",
    "description": "Full description...",
    "content": "Full content...",
    "url": "https://...",
    "published_at": datetime(2024, 10, 18),
    "author": "John Doe",
    "currencies": ["BTC", "ETH"],  # Mentioned coins
    "sentiment": "bullish",  # bullish, bearish, neutral
    "sentiment_score": 0.75,  # -1 to 1
    "impact": 8,  # 1-10 scale
    "engagement": {  # If applicable
        "likes": 1000,
        "comments": 50,
        "shares": 200
    },
    "metadata": {
        # Source-specific data
    }
}
```

---

## 🚀 **Quick Start Example**

```python
import asyncio
import logging
from sources import (
    CryptoPanicSource,
    NewsAPISource,
    TwitterScraperSource,
    RedditScraperSource,
    RSSFeedSource
)

async def collect_all_news():
    logger = logging.getLogger(__name__)
    
    # Initialize sources
    cryptopanic = CryptoPanicSource(api_key="your_key", logger=logger)
    newsapi = NewsAPISource(api_key="your_key", logger=logger)
    twitter = TwitterScraperSource(logger=logger)
    reddit = RedditScraperSource(
        client_id="id",
        client_secret="secret",
        user_agent="app"
    )
    rss = RSSFeedSource(logger=logger)
    
    # Collect from all sources
    all_articles = []
    
    # CryptoPanic
    all_articles.extend(await cryptopanic.fetch_posts(limit=50))
    
    # NewsAPI
    all_articles.extend(await newsapi.get_crypto_news(hours_back=24))
    
    # Twitter
    all_articles.extend(await twitter.search_crypto_tweets(hours_back=24))
    
    # Reddit
    all_articles.extend(await reddit.scrape_all_crypto_subs())
    
    # RSS
    all_articles.extend(await rss.fetch_all_feeds())
    
    print(f"Collected {len(all_articles)} articles from all sources")
    
    # Filter high-impact only
    high_impact = [a for a in all_articles if a.get("impact", 0) >= 7]
    print(f"Found {len(high_impact)} high-impact articles")
    
    return all_articles

# Run
asyncio.run(collect_all_news())
```

---

## 📈 **Features Summary**

| Feature | CryptoPanic | NewsAPI | Twitter | Reddit | RSS |
|---------|-------------|---------|---------|--------|-----|
| Free Tier | ✅ 50/day | ✅ 100/day | ✅ Unlimited | ✅ Yes | ✅ Unlimited |
| API Key Required | Optional | Yes | No* | Yes | No |
| Crypto-Specific | ✅ | ❌ | ✅ | ✅ | ✅ |
| Real-time | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sentiment | ✅ | ⚠️ Basic | ✅ | ✅ | ⚠️ Basic |
| Engagement | ✅ | ❌ | ✅ | ✅ | ❌ |
| Historical | ✅ | ✅ | ✅ | ✅ | ✅ |

*Twitter can work without API using snscrape

---

## ✅ **All Sources Complete!**

You now have **5 fully functional news sources** ready to collect crypto news from:
1. ✅ **CryptoPanic** - Crypto aggregator with sentiment
2. ✅ **NewsAPI** - General news from 50K+ sources
3. ✅ **Twitter** - Social sentiment & influencers
4. ✅ **Reddit** - Community discussions
5. ✅ **RSS** - Direct from 12 crypto news sites

**Next Steps:**
- Build the `collector.py` (orchestrator)
- Build parsers (HTML, article extraction)
- Build storage writer (MySQL)
- Complete main.py and config.yaml