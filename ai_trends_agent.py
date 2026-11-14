#!/usr/bin/env python3
"""
AI Trends Agent for Meevo
Collects, scores, and ranks AI trends/releases by business impact.
Detects commercial bias and flags sources with product pitches.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import anthropic

# Initialize Claude client
client = anthropic.Anthropic()

def detect_commercial_intent(title: str, summary: str, url: str, source: str) -> dict:
    """
    Detect if an item or source has commercial intent.
    Returns: {has_commercial_intent: bool, severity: str, beneficiary: str, note: str}
    """
    commercial_keywords = [
        "sign up", "try free", "upgrade", "pricing", "get started",
        "limited offer", "exclusive", "affiliate", "sponsored",
        "partnership", "integrates with", "powered by"
    ]

    text_to_check = f"{title} {summary}".lower()

    # Check for commercial language
    commercial_score = sum(1 for kw in commercial_keywords if kw in text_to_check)

    # Check if URL goes to product/pricing pages
    product_urls = [
        "/pricing", "/products", "/tools", "/signup", "/try",
        "product-hunt", "producthunt", ".com/", "app.", "dashboard."
    ]
    url_lower = url.lower()
    has_product_url = any(pattern in url_lower for pattern in product_urls)

    # Check source credibility
    biased_sources = {
        "Newsletter sponsored": "high",
        "Product announcement": "high",
        "Company blog": "medium",
    }

    if commercial_score >= 3 or has_product_url:
        return {
            "has_commercial_intent": True,
            "severity": "high" if commercial_score >= 3 else "medium",
            "beneficiary": extract_beneficiary(title, source),
            "note": "⚠️ Source appears to have commercial motivation"
        }

    return {
        "has_commercial_intent": False,
        "severity": "low",
        "beneficiary": None,
        "note": None
    }


def extract_beneficiary(title: str, source: str) -> Optional[str]:
    """Extract which product/company is being promoted."""
    # Simple heuristic - in real version, use NER or Claude
    if "anthropic" in title.lower() or "claude" in title.lower():
        return "Anthropic/Claude"
    if "openai" in title.lower() or "gpt" in title.lower():
        return "OpenAI"
    if "google" in title.lower() or "gemini" in title.lower():
        return "Google"
    if "meta" in title.lower() or "llama" in title.lower():
        return "Meta"
    return None


def score_item(item: dict) -> dict:
    """
    Score an item using Claude API.
    Returns scores for: cost, competitive, expectation + reasoning.
    """

    prompt = f"""Analyze this AI news item for Meevo (a business AI assistant platform built on Claude):

TITLE: {item['title']}
SOURCE: {item['source']}
SUMMARY: {item['summary']}
URL: {item['url']}

Score this on THREE independent axes (1-5 each, where 5 is highest impact):

1. **Cost/Capability Impact** (Does it affect Meevo's operations?)
   - 5 = Direct impact on Claude API cost, rate limits, or core capabilities
   - 4 = New model tier or major feature that affects users
   - 3 = Moderate: API feature or token efficiency improvement
   - 2 = Minor: Beta feature or incremental improvement
   - 1 = Not applicable

2. **Competitive Threat** (Do competitors gain advantage?)
   - 5 = Competitor launches feature Meevo doesn't have
   - 4 = Competitor announces roadmap feature launching soon
   - 3 = Competitor improves existing features meaningfully
   - 2 = Incremental competitor improvement
   - 1 = Not a threat

3. **Customer Expectation** (Will Meevo's users ask for this?)
   - 5 = Major capability shift everyone will talk about
   - 4 = Feature launching broadly that users will expect Meevo to support
   - 3 = Feature some users will ask about
   - 2 = Niche feature (cool but not urgent)
   - 1 = Unlikely to be requested

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "cost_score": <1-5>,
  "competitive_score": <1-5>,
  "expectation_score": <1-5>,
  "category": "<model_release|pricing|research|tool_launch|regulation|benchmark|safety>",
  "reasoning": "<2-3 sentences explaining the scores>"
}}"""

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    try:
        result = json.loads(response.content[0].text)
        return result
    except json.JSONDecodeError:
        # Fallback if Claude returns invalid JSON
        return {
            "cost_score": 2,
            "competitive_score": 2,
            "expectation_score": 2,
            "category": "research",
            "reasoning": "Unable to parse scoring."
        }


def calculate_final_score(scores: dict, days_old: int) -> float:
    """
    Calculate final composite score.
    Formula: (cost * 0.35 + competitive * 0.35 + expectation * 0.30) * 10 + freshness_boost
    """
    base_score = (
        scores["cost_score"] * 0.35 +
        scores["competitive_score"] * 0.35 +
        scores["expectation_score"] * 0.30
    ) * 10

    # Freshness: max +10 points for today, decays over 30 days
    freshness_boost = max(0, 10 - (days_old * 0.33))

    return round(base_score + freshness_boost, 1)


def process_items(raw_items: list) -> list:
    """Score all items and add metadata."""
    processed = []

    for item in raw_items:
        # Calculate days old
        item_date = datetime.fromisoformat(item["date"])
        days_old = (datetime.now() - item_date).days

        # Get scores from Claude
        scores = score_item(item)

        # Calculate final score
        final_score = calculate_final_score(scores, days_old)

        # Detect commercial intent
        commercial = detect_commercial_intent(
            item["title"],
            item["summary"],
            item["url"],
            item["source"]
        )

        processed_item = {
            **item,
            "days_old": days_old,
            "scores": scores,
            "final_score": final_score,
            "commercial_intent": commercial
        }

        processed.append(processed_item)

    # Sort by final score descending
    processed.sort(key=lambda x: x["final_score"], reverse=True)

    return processed


def generate_coverage_stats(items: list) -> dict:
    """Generate coverage breakdown and trend analysis."""
    sources = {}
    categories = {}
    commercial_count = 0

    for item in items:
        source = item["source"]
        sources[source] = sources.get(source, 0) + 1

        category = item["scores"].get("category", "other")
        categories[category] = categories.get(category, 0) + 1

        if item["commercial_intent"]["has_commercial_intent"]:
            commercial_count += 1

    return {
        "total_items": len(items),
        "avg_score": round(sum(i["final_score"] for i in items) / len(items), 1) if items else 0,
        "commercial_intent_items": commercial_count,
        "source_breakdown": sources,
        "category_breakdown": categories,
        "top_source": max(sources, key=sources.get) if sources else None
    }


def generate_report(items: list, week_str: str) -> dict:
    """Generate the complete weekly report."""

    stats = generate_coverage_stats(items)

    return {
        "week": week_str,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_items": stats["total_items"],
            "avg_score": stats["avg_score"],
            "commercial_intent_items": stats["commercial_intent_items"],
            "top_category": stats["top_category_breakdown"],
            "top_source": stats["top_source"],
            "note": "Items flagged with ⚠️ have commercial motivation. Filter them out for unbiased view."
        },
        "coverage_breakdown": {
            "by_source": stats["source_breakdown"],
            "by_category": stats["category_breakdown"]
        },
        "items": items
    }


def main():
    """Main execution."""

    # For now, use mocked data (will integrate real feeds later)
    mock_items = [
        {
            "title": "Claude 4.1 Released with Extended Context",
            "source": "Anthropic",
            "url": "https://www.anthropic.com/news/claude-4-1",
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "summary": "Anthropic announces Claude 4.1 with 200K context window and improved reasoning."
        },
        {
            "title": "OpenAI Announces GPT-4.5 with Reasoning",
            "source": "OpenAI Blog",
            "url": "https://openai.com/blog/gpt-4-5",
            "date": (datetime.now() - timedelta(days=2)).isoformat(),
            "summary": "New GPT-4.5 model with extended thinking and 128K context. Try it free with signup."
        },
        {
            "title": "Google Releases Gemini 3 with Agentic Capabilities",
            "source": "The Verge",
            "url": "https://www.theverge.com/ai/2026/11/13/gemini-3",
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "summary": "Google's new Gemini 3 can plan multi-step tasks. Competitors rushing to match features."
        },
        {
            "title": "New Research: Efficient LLM Fine-tuning Techniques",
            "source": "ArXiv",
            "url": "https://arxiv.org/abs/2311.00000",
            "date": (datetime.now() - timedelta(days=4)).isoformat(),
            "summary": "Researchers publish breakthrough in parameter-efficient fine-tuning. 50% less compute required."
        },
        {
            "title": "EU Proposes AI Regulation Framework",
            "source": "Reuters",
            "url": "https://www.reuters.com/technology/eu-ai-2026/",
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "summary": "European Union proposes mandatory safety audits for large language models by 2027."
        }
    ]

    print("🤖 AI Trends Agent - Processing items...")
    processed_items = process_items(mock_items)

    week_str = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    report = generate_report(processed_items, week_str)

    # Save report
    with open("ai_trends_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Report generated: ai_trends_report.json")
    print(f"📊 Stats: {report['summary']['total_items']} items, avg score {report['summary']['avg_score']}/10")
    print(f"⚠️  Commercial intent items: {report['summary']['commercial_intent_items']}")


if __name__ == "__main__":
    main()
