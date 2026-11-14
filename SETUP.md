# AI Trends Dashboard - Setup Guide

## Overview

This is a production-ready system for tracking AI trends and releases, ranked by business impact to Meevo, with automatic bias detection.

**Components:**
- `ai_trends_production.py` — Weekly data collection & scoring agent
- `dashboard.html` — Interactive dashboard (Netlify-hosted)
- `.github/workflows/ai_trends.yml` — Automated weekly execution

---

## Quick Start (Local Testing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Run Once
```bash
python ai_trends_production.py
```

This generates `ai_trends_report.json` and updates the dashboard.

---

## Production Deployment

### Option A: GitHub + Netlify (Recommended)

**Prerequisites:**
- GitHub repository with this code
- Netlify account
- Anthropic API key

**Setup Steps:**

1. **Create GitHub secrets:**
   ```
   Settings → Secrets → New Repository Secret
   - ANTHROPIC_API_KEY: <your-anthropic-key>
   - NETLIFY_AUTH_TOKEN: <your-netlify-token>
   - NETLIFY_SITE_ID: <your-netlify-site-id>
   ```

2. **Move workflow file:**
   ```bash
   mkdir -p .github/workflows
   mv .github_workflows_ai_trends.yml .github/workflows/ai_trends.yml
   ```

3. **Get Netlify credentials:**
   - Go to https://app.netlify.com/user/applications
   - Create "Personal access tokens" → Copy token → Add to GitHub secrets as `NETLIFY_AUTH_TOKEN`
   - Site ID: netlify.com → Site → Site Settings → "API ID" → Copy → Add as `NETLIFY_SITE_ID`

4. **Test workflow:**
   - Go to repo → Actions → "AI Trends Weekly Update" → "Run workflow"

5. **Schedule is automatic:**
   - Every Sunday 6 PM UTC (18:00)
   - Or manually trigger anytime

---

### Option B: AWS Lambda (Scheduled)

If you prefer serverless without GitHub:

1. **Package for Lambda:**
   ```bash
   zip -r lambda.zip ai_trends_production.py requirements.txt dashboard.html
   ```

2. **Create Lambda function:**
   - Runtime: Python 3.11
   - Upload zip
   - Add environment variable: `ANTHROPIC_API_KEY`
   - Memory: 512 MB
   - Timeout: 60 seconds

3. **Add S3 trigger:**
   - Lambda → Add trigger → CloudWatch Events
   - Schedule: `cron(0 18 * * ? *)` (Sunday 6 PM UTC)

4. **Lambda function code:**
   ```python
   import json
   import boto3
   from ai_trends_production import main

   s3 = boto3.client('s3')

   def lambda_handler(event, context):
       report = main()
       
       # Upload to S3
       s3.put_object(
           Bucket='your-bucket',
           Key='ai_trends_report.json',
           Body=json.dumps(report),
           ContentType='application/json'
       )
       
       return {'statusCode': 200, 'body': 'Success'}
   ```

---

### Option C: Local Cron Job

Run weekly on your machine:

1. **Edit crontab:**
   ```bash
   crontab -e
   ```

2. **Add entry (Sunday 6 PM):**
   ```
   0 18 * * 0 cd /path/to/project && /usr/bin/python3 ai_trends_production.py >> logs/trends.log 2>&1
   ```

3. **Manual sync to Netlify:**
   - Use `netlify deploy --prod` to publish updated `ai_trends_report.json`

---

## Customization

### Change Data Sources

Edit `SOURCES` dict in `ai_trends_production.py`:

```python
SOURCES = {
    "rss": {
        "My Custom Source": "https://example.com/feed.xml",
        # Add your sources here
    }
}
```

### Adjust Scoring Weights

In `calculate_final_score()`:

```python
# Default: 35% cost, 35% competitive, 30% expectation
base_score = (cost * 0.35 + competitive * 0.35 + expectation * 0.30) * 10

# Try this for more competitive focus:
base_score = (cost * 0.30 + competitive * 0.40 + expectation * 0.30) * 10
```

### Modify Commercial Bias Keywords

Edit `commercial_keywords` in `detect_commercial_intent()`:

```python
commercial_keywords = [
    "sign up", "try free", "upgrade",  # Add/remove as needed
    # Add your keywords here
]
```

### Change Schedule

In `.github/workflows/ai_trends.yml`:

```yaml
- cron: '0 18 * * 0'  # Sunday 6 PM UTC
# Examples:
# - cron: '0 9 * * 1'   # Monday 9 AM UTC
# - cron: '0 0 * * *'   # Daily at midnight UTC
```

---

## Monitoring & Debugging

### Check if scoring works:
```bash
python ai_trends_production.py
```

Look for:
- ✅ "Found X RSS items + Y HN items"
- ✅ "After dedup: Z unique items"
- ✅ "Scoring with Claude..."
- ✅ "Report generated"

### Common Issues:

**"Could not resolve authentication method"**
- Ensure `ANTHROPIC_API_KEY` is set
- Test: `echo $ANTHROPIC_API_KEY`

**"No items found"**
- RSS feeds might be down. Try manually:
  ```python
  import feedparser
  feedparser.parse("https://feed-url.xml")
  ```

**Dashboard not updating**
- Check GitHub Actions logs
- Ensure `NETLIFY_SITE_ID` is correct
- Test Netlify deploy: `netlify deploy --prod`

---

## Dashboard Usage

**View at:** `https://your-netlify-site.netlify.app`

**Filters:**
- **Impact Level:** High (8+), Medium (5-7), Low (<5)
- **Category:** Model release, Pricing, Research, Tool launch, Regulation, Benchmark, Safety
- **Bias & Transparency:** Hide/Show commercially-motivated items

**Read:**
- Score breakdown (Cost/Competitive/Expectation) for each item
- Commercial intent flags (yellow warning banner)
- Reasoning for each score
- Coverage breakdown (% by source and category)

---

## Maintenance

### Weekly (Automatic)
- Data collection & scoring runs
- Report generated & dashboard updated

### Monthly (Manual)
- Review coverage breakdown — any sources you'd like to add/remove?
- Check accuracy of scores — adjust commercial keyword list if needed
- Look for patterns — what's actually impacting Meevo?

### Quarterly (Strategic)
- Analyze which items you acted on vs. scored high
- Refine scoring rubric based on actual impact
- Adjust source weighting (cost vs. competitive vs. expectation)

---

## Architecture

```
RSS Feeds / HN API
       ↓
   Collect Items (5 per source)
       ↓
   Deduplicate by URL
       ↓
   Score with Claude (batch of 5)
       ↓
   Detect Commercial Bias
       ↓
   Calculate Composite Score
       ↓
   Generate ai_trends_report.json
       ↓
   (GitHub Actions) Commit & Push
       ↓
   (Netlify) Auto-deploy dashboard.html
       ↓
   Live at your-site.netlify.app
```

---

## Cost Estimation

**Anthropic API:**
- ~10-20 items per week
- ~2-3 Claude calls per item (batch of 5)
- ~500 tokens per call
- **Cost:** ~$0.02 per week (~$1/year)

**Netlify:**
- Static site hosting: Free tier sufficient
- 1 auto-deploy per week: Free

**Total:** Essentially free (API costs are negligible)

---

## Next Steps

1. **Try locally first:** `python ai_trends_production.py`
2. **Choose deployment:** GitHub+Netlify (easiest) or Lambda or cron
3. **Set it up:** Follow Option A/B/C above
4. **Test once:** Manually trigger, verify dashboard updates
5. **Let it run:** Check back in 2-3 weeks to refine scores

Questions? Check the reasoning for low/high items to understand the scoring model.
