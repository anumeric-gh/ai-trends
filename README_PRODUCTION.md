# 🤖 AI Trends Agent for Meevo

A weekly AI trends & releases tracker that automatically collects, scores, and ranks items by business impact. **Detects and flags commercial bias** so you see unbiased intelligence.

## What It Does

Every Sunday at 6 PM UTC:
1. ✅ Collects latest AI news from 10+ sources (RSS, HN, newsletters)
2. ✅ Scores each item for business impact using Claude
3. ✅ Detects which items have commercial motivation
4. ✅ Publishes interactive dashboard
5. ✅ Archives historical data for trend analysis

**Three scoring vectors:**
- **Cost/Capability:** Does it affect your Claude dependency?
- **Competitive:** Are competitors gaining advantage?
- **Customer Expectation:** Will users ask for this?

## Key Features

🔍 **Bias Detection** — Items with commercial motivation flagged in yellow  
🎯 **Three-Vector Scoring** — See the breakdown of why each item ranks where it does  
📊 **Coverage Transparency** — See what % of signals come from each source  
🔘 **Smart Filters** — Hide commercial items, filter by category/impact level  
📈 **Weekly Cadence** — Automatic, no manual work needed  
💰 **Cheap** — ~$0.02/week in Claude API costs  

## Quick Start

### Local Testing
```bash
# 1. Install
pip install -r requirements.txt

# 2. Set key
export ANTHROPIC_API_KEY="sk-..."

# 3. Run
python ai_trends_production.py

# 4. View
open dashboard.html
```

### Production Deployment

**Easiest: GitHub + Netlify**
1. Push this repo to GitHub
2. Add GitHub secrets (API key, Netlify tokens)
3. Move `.github_workflows_ai_trends.yml` to `.github/workflows/ai_trends.yml`
4. Done — runs automatically every Sunday

→ See [SETUP.md](SETUP.md) for detailed instructions and alternatives (Lambda, cron)

## Files

| File | Purpose |
|------|---------|
| `ai_trends_production.py` | Main agent: collects data, scores, generates report |
| `dashboard.html` | Interactive web dashboard (Netlify-hosted) |
| `ai_trends_report.json` | Output data (auto-generated weekly) |
| `requirements.txt` | Python dependencies |
| `.github/workflows/ai_trends.yml` | GitHub Actions automation |
| `SETUP.md` | Deployment & customization guide |

## Dashboard Preview

```
🤖 AI Trends for Meevo — Week of Nov 13

📊 This Week's Signals
• 12 items tracked
• Avg impact score: 6.2/10
• Top category: Model Releases (40%)

🔴 HIGH IMPACT (8+)
1. OpenAI Announces GPT-4.5 — 8.3/10
   ⚠️ Source appears to have commercial motivation
   Impact: Cost(4) Competitive(5) Expectation(5)

2. Claude 4.1 Released — 7.9/10
   Impact: Cost(5) Competitive(3) Expectation(4)
   💭 Direct impact on Meevo's core capability.

🟡 MEDIUM IMPACT (5–7)
3. Google Releases Gemini 3 — 6.7/10
4. [...]

📊 Coverage Breakdown
By Source: Anthropic(20%) OpenAI(20%) Google(20%) ArXiv(20%) Reuters(20%)
By Category: Model(40%) Research(20%) Tool(20%) Regulation(20%)
```

## Scoring Examples

**High Impact (7+):**
- ✅ Claude/OpenAI price drop → Cost: 5
- ✅ Competitor launches agent mode → Competitive: 5
- ✅ New model everyone's talking about → Expectation: 5

**Medium Impact (5–7):**
- 🟡 Google improves existing features → Competitive: 3–4
- 🟡 Academic research on optimization → Cost: 2–3
- 🟡 Users will eventually ask → Expectation: 3–4

**Low Impact (<5):**
- ❌ Niche research paper → Expectation: 1–2
- ❌ Minor competitor update → Competitive: 1–2
- ❌ Unrelated AI news → All: 1–2

## Customization

**Want different sources?**
- Edit `SOURCES` in `ai_trends_production.py`

**Want different weights?**
- Adjust cost/competitive/expectation percentages in `calculate_final_score()`

**Want to catch different bias keywords?**
- Edit `commercial_keywords` in `detect_commercial_intent()`

**Want to change schedule?**
- Update cron in `.github/workflows/ai_trends.yml`

See [SETUP.md](SETUP.md) for details.

## How It Detects Bias

Commercial intent flagged if item has:
- Keywords: "sign up", "try free", "pricing", "limited offer", etc.
- URLs with: `/pricing`, `/products`, `/signup`, `/try`, `app.`
- Beneficiary: OpenAI, Google, etc. (extracted from title)

**Examples:**
- ✅ OpenAI blog: "New GPT-4.5. Try it free with signup." → FLAGGED (has "try free" + "signup")
- ✅ Anthropic: "Claude 4.1 with 200K context" → NOT FLAGGED (neutral announcement)
- ✅ HN: "GPT-4.5 raises the bar" → NOT FLAGGED (third-party perspective)

## Understanding Scores

Each item gets three independent 1–5 scores:

**Cost/Capability (35% weight)**
- 5 = Direct impact (pricing, rate limits, major features)
- 4 = New tier/capability affecting users
- 3 = API feature, efficiency gain
- 2 = Minor, beta feature
- 1 = Not applicable

**Competitive (35% weight)**
- 5 = Competitor has feature you don't
- 4 = Competitor announces roadmap feature coming soon
- 3 = Competitor improves existing features
- 2 = Incremental improvement
- 1 = Not a threat

**Expectation (30% weight)**
- 5 = Capability shift everyone talks about
- 4 = Feature launching broadly, users expect
- 3 = Some users will ask
- 2 = Niche, cool but not urgent
- 1 = Unlikely requested

**Final Score = (Cost × 0.35 + Competitive × 0.35 + Expectation × 0.30) × 10 + freshness_boost**

**Color coding:**
- 🔴 **High:** 8–10 (red border)
- 🟡 **Medium:** 5–7 (orange border)
- 🟢 **Low:** <5 (gray border)

## Running Manually

```bash
# Test the full pipeline
python ai_trends_production.py

# You'll see:
# 📡 Collecting data from sources...
#   Found 25 RSS items + 8 HN items
#   After dedup: 30 unique items
# 🧠 Scoring with Claude...
# ✅ Report generated: ai_trends_report.json
#    Total items: 30
#    Avg score: 6.8/10
#    Commercial intent: 4
#    Top category: model_release
```

Then open `dashboard.html` to view the results.

## Troubleshooting

**No items showing up?**
- Check internet connection to RSS feeds
- Verify API key is set: `echo $ANTHROPIC_API_KEY`
- Try running locally first

**GitHub Actions not running?**
- Check secrets are set (Settings → Secrets)
- Look at Actions tab for error logs
- Try "Run workflow" button to trigger manually

**Dashboard not updating?**
- Verify `ai_trends_report.json` was generated
- Check Netlify deploy logs
- Ensure GitHub push succeeded

See [SETUP.md](SETUP.md) for more details.

## Cost

| Component | Cost | Notes |
|-----------|------|-------|
| Claude API | ~$0.02/week | 10-20 items × 2-3 API calls × ~500 tokens |
| Netlify | $0 | Free tier sufficient for static site |
| GitHub Actions | $0 | Included with repo |
| **Total** | **~$1/year** | Essentially free |

## Next Steps

1. **Try it locally:** `python ai_trends_production.py`
2. **Choose hosting:** GitHub+Netlify (easy) or Lambda (scalable) or cron (simple)
3. **Deploy:** Follow [SETUP.md](SETUP.md)
4. **Refine:** After 2-3 weeks, adjust scores based on actual impact
5. **Archive:** Keep historical data to spot trends over time

---

**Questions?** Check the reasoning in each item — it explains why it scored as it did.

**Feedback?** The scoring is opinionated for Meevo. Adjust weights/sources/keywords to match your priorities.
