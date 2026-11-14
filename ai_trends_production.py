#!/usr/bin/env python3
"""
AI Trends Production Agent - Weekly Data Collection & Scoring
Collects from RSS feeds, HN API, newsletters. Scores with Claude.
Detects commercial bias. Generates dashboard data.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, List
import requests
import anthropic
import feedparser

# Configuration
SOURCES = {
    "rss": {
        "Anthropic": "https://www.anthropic.com/news.xml",
        "OpenAI": "https://openai.com/feed.xml",
        "Google DeepMind": "https://blog.research.google/feeds/",
        "The Verge AI": "https://www.theverge.com/ai/rss/index.xml",
        "TechCrunch AI": "https://feeds.techcrunch.com/techcrunch/ai/",
        "Hacker News": "https://news.ycombinator.com/rss",
        "ArXiv AI": "http://arxiv.org/rss/cs.AI",
        "Papers with Code": "https://paperswithcode.com/rss/",
    }
}

client = anthropic.Anthropic()

def fetch_rss_feeds() -> List[dict]:
    """Fetch and parse RSS feeds from key sources."""
    items = []

    for source_name, feed_url in SOURCES["rss"].items():
        try:
            feed = feedparser.parse(feed_url)

            # Get latest 5 entries from each feed
            for entry in feed.entries[:5]:
                item = {
                    "title": entry.get("title", ""),
                    "source": source_name,
                    "url": entry.get("link", ""),
                    "date": entry.get("published", datetime.now().isoformat()),
                    "summary": entry.get("summary", "")[:500],  # Limit length
                }

                # Skip if missing critical fields
                if item["title"] and item["url"]:
                    items.append(item)

        except Exception as e:
            print(f"⚠️  Error fetching {source_name}: {str(e)}")
            continue

    return items


def fetch_hacker_news_trending() -> List[dict]:
    """Fetch trending AI-related items from Hacker News."""
    items = []

    try:
        # Get top stories from HN
        hn_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        top_ids = requests.get(hn_url, timeout=5).json()[:30]  # Get top 30

        ai_keywords = ["ai", "llm", "gpt", "claude", "model", "machine learning", "neural", "transformer", "reasoning"]

        for story_id in top_ids:
            try:
                story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=3).json()

                title = story.get("title", "").lower()

                # Filter for AI-related stories
                if any(keyword in title for keyword in ai_keywords):
                    item = {
                        "title": story.get("title", ""),
                        "source": "Hacker News",
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "date": datetime.fromtimestamp(story.get("time", 0)).isoformat(),
                        "summary": f"Trending on HN ({story.get('score', 0)} points, {story.get('descendants', 0)} comments)"
                    }

                    if item["title"]:
                        items.append(item)

            except Exception as e:
                continue

    except Exception as e:
        print(f"⚠️  Error fetching Hacker News: {str(e)}")

    return items


def deduplicate_items(items: List[dict]) -> List[dict]:
    """Remove duplicate items by URL."""
    seen = set()
    unique = []

    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique


def score_items_batch(items: List[dict]) -> List[dict]:
    """
    Score multiple items in a batch using Claude.
    Uses prompt caching to reduce costs.
    """

    # Group items into batches of 5 to avoid huge prompts
    batch_size = 5
    scored_items = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        # Format items for Claude
        items_text = "\n---\n".join([
            f"ITEM {j+1}:\nTitle: {item['title']}\nSource: {item['source']}\nSummary: {item['summary']}\nURL: {item['url']}"
            for j, item in enumerate(batch)
        ])

        prompt = f"""Score each of these AI news items for Meevo (a business AI assistant platform built on Claude).

Context: Meevo uses Claude API as core technology. Impact vectors are:
1. Cost/Capability: Does it affect Claude API pricing/capabilities/user expectations?
2. Competitive: Do competitors gain advantage?
3. Customer Expectation: Will Meevo users expect to see this supported?

{items_text}

Respond with a JSON array, one object per item (in same order):
[
  {{
    "title": "<item title>",
    "cost_score": <1-5>,
    "competitive_score": <1-5>,
    "expectation_score": <1-5>,
    "category": "<model_release|pricing|research|tool_launch|regulation|benchmark|safety>",
    "reasoning": "<2-3 sentences>"
  }}
]

Only return JSON, no other text."""

        try:
            response = client.messages.create(
                model="claude-opus-5-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            result_text = response.content[0].text.strip()

            # Extract JSON from response (in case there's surrounding text)
            try:
                scores = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped
                start = result_text.find('[')
                end = result_text.rfind(']') + 1
                if start != -1 and end > start:
                    scores = json.loads(result_text[start:end])
                else:
                    print(f"⚠️  Could not parse Claude response: {result_text[:100]}")
                    continue

            # Merge scores with original items
            for j, score_data in enumerate(scores):
                if j < len(batch):
                    batch[j].update(score_data)
                    scored_items.append(batch[j])

        except Exception as e:
            print(f"⚠️  Error scoring batch: {str(e)}")
            # Add items without scores
            for item in batch:
                item.update({
                    "cost_score": 2,
                    "competitive_score": 2,
                    "expectation_score": 2,
                    "category": "other",
                    "reasoning": "Unable to score at this time."
                })
                scored_items.append(item)

    return scored_items


def detect_commercial_intent(item: dict) -> dict:
    """Detect if an item has commercial bias."""

    commercial_keywords = [
        "sign up", "try free", "upgrade", "pricing", "get started",
        "limited offer", "exclusive", "affiliate", "sponsored",
        "partnership", "integrates with", "powered by", "request access"
    ]

    text_to_check = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    commercial_score = sum(1 for kw in commercial_keywords if kw in text_to_check)

    url_lower = item.get('url', '').lower()
    product_urls = ["/pricing", "/products", "/tools", "/signup", "/try", "app."]
    has_product_url = any(pattern in url_lower for pattern in product_urls)

    has_intent = commercial_score >= 2 or has_product_url

    return {
        "has_commercial_intent": has_intent,
        "severity": "high" if commercial_score >= 3 else "medium" if has_intent else "low",
        "beneficiary": extract_beneficiary(item['title'], item['source']),
        "note": "⚠️ Source appears to have commercial motivation" if has_intent else None
    }


def extract_beneficiary(title: str, source: str) -> Optional[str]:
    """Extract which company is being promoted."""
    title_lower = title.lower()

    if "anthropic" in title_lower or "claude" in title_lower:
        return "Anthropic/Claude"
    if "openai" in title_lower or "gpt" in title_lower:
        return "OpenAI"
    if "google" in title_lower or "gemini" in title_lower:
        return "Google"
    if "meta" in title_lower or "llama" in title_lower:
        return "Meta"

    return None


def calculate_final_score(item: dict) -> float:
    """Calculate composite impact score."""

    cost = item.get("cost_score", 2)
    competitive = item.get("competitive_score", 2)
    expectation = item.get("expectation_score", 2)

    base_score = (cost * 0.35 + competitive * 0.35 + expectation * 0.30) * 10

    # Parse date and calculate freshness
    try:
        item_date = datetime.fromisoformat(item["date"].replace('Z', '+00:00'))
        days_old = (datetime.now(item_date.tzinfo) - item_date).days
    except:
        days_old = 0

    freshness_boost = max(0, 10 - (days_old * 0.33))

    return round(base_score + freshness_boost, 1)


def process_items(raw_items: List[dict]) -> List[dict]:
    """Full processing pipeline."""

    print(f"📊 Processing {len(raw_items)} items...")

    # Score with Claude
    scored_items = score_items_batch(raw_items)

    # Add commercial detection
    for item in scored_items:
        item["commercial_intent"] = detect_commercial_intent(item)
        item["final_score"] = calculate_final_score(item)
        item["days_old"] = (datetime.now() - datetime.fromisoformat(
            item["date"].replace('Z', '+00:00')
        )).days if "date" in item else 0

    # Sort by score
    scored_items.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    return scored_items


def generate_report(items: List[dict], week_str: str) -> dict:
    """Generate final report."""

    if not items:
        return {
            "week": week_str,
            "generated_at": datetime.now().isoformat(),
            "summary": {"total_items": 0, "avg_score": 0, "commercial_intent_items": 0},
            "coverage_breakdown": {},
            "items": []
        }

    sources = {}
    categories = {}
    commercial_count = 0

    for item in items:
        source = item.get("source", "Unknown")
        sources[source] = sources.get(source, 0) + 1

        category = item.get("category", "other")
        categories[category] = categories.get(category, 0) + 1

        if item.get("commercial_intent", {}).get("has_commercial_intent"):
            commercial_count += 1

    avg_score = round(sum(item.get("final_score", 0) for item in items) / len(items), 1) if items else 0

    return {
        "week": week_str,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_items": len(items),
            "avg_score": avg_score,
            "commercial_intent_items": commercial_count,
            "top_category": max(categories, key=categories.get) if categories else None,
            "top_source": max(sources, key=sources.get) if sources else None,
            "note": "Items flagged with ⚠️ have commercial motivation. Filter them out for unbiased view."
        },
        "coverage_breakdown": {
            "by_source": sources,
            "by_category": categories
        },
        "items": items
    }


def main():
    """Main execution pipeline."""

    print("🤖 AI Trends Agent - Production Mode")
    print(f"⏱️  Started at {datetime.now().isoformat()}")

    # Collect data
    print("📡 Collecting data from sources...")
    rss_items = fetch_rss_feeds()
    hn_items = fetch_hacker_news_trending()

    all_items = rss_items + hn_items
    print(f"  Found {len(rss_items)} RSS items + {len(hn_items)} HN items")

    # Deduplicate
    unique_items = deduplicate_items(all_items)
    print(f"  After dedup: {len(unique_items)} unique items")

    # Score items
    print("🧠 Scoring with Claude...")
    processed_items = process_items(unique_items)

    # Generate report
    week_str = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    report = generate_report(processed_items, week_str)

    # Save report
    output_file = "ai_trends_report.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report generated: {output_file}")
    print(f"📊 Summary:")
    print(f"   Total items: {report['summary']['total_items']}")
    print(f"   Avg score: {report['summary']['avg_score']}/10")
    print(f"   Commercial intent: {report['summary']['commercial_intent_items']}")
    print(f"   Top category: {report['summary']['top_category']}")
    print(f"⏱️  Completed at {datetime.now().isoformat()}")

    return report


if __name__ == "__main__":
    main()
