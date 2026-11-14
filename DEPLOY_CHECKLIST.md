# Deployment Checklist

## What You Have

✅ **Prototype & Dashboard**
- `dashboard.html` — Interactive web interface (demo data embedded)
- `ai_trends_report.json` — Sample output (from demo)

✅ **Production Code**
- `ai_trends_production.py` — Real data collection + Claude scoring
- `requirements.txt` — Dependencies
- `.github_workflows_ai_trends.yml` — GitHub Actions workflow
- `SETUP.md` — Detailed deployment guide
- `README_PRODUCTION.md` — Full documentation

✅ **Built-in Features**
- RSS feed collection from 8 sources
- Hacker News API integration
- Batch scoring with Claude
- Commercial bias detection
- Weekly automation
- Netlify deployment

---

## To Get Running (Choose One Path)

### Path A: Test Locally (15 min)
Best for: Seeing if it works before committing to production

**Steps:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Run the agent
python ai_trends_production.py

# 4. View results
open dashboard.html
```

**Expected output:**
```
✅ Report generated: ai_trends_report.json
📊 Summary:
   Total items: 12–20 (depends on what's published this week)
   Avg score: 6.5–7.5/10
   Commercial intent: 2–4 items
```

**What happens:** Fetches current items from RSS/HN, scores them with Claude (~$0.02), generates JSON, you view in browser.

---

### Path B: GitHub + Netlify (1 hour)
Best for: Fully automated weekly runs

**Prerequisites:**
- GitHub account (repo with this code pushed)
- Netlify account (free tier)
- Anthropic API key

**Steps:**

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial AI trends agent setup"
   git remote add origin https://github.com/YOUR_ACCOUNT/ai-trends.git
   git push -u origin main
   ```

2. **Get secrets:**
   - Anthropic API key from dashboard
   - Netlify personal token: https://app.netlify.com/user/applications
   - Netlify site ID: Netlify → Site → Settings → API ID

3. **Add GitHub secrets:**
   - Repo → Settings → Secrets → "New repository secret"
   - Add three:
     - `ANTHROPIC_API_KEY` = your API key
     - `NETLIFY_AUTH_TOKEN` = your netlify token
     - `NETLIFY_SITE_ID` = your site ID

4. **Set up workflow:**
   ```bash
   mkdir -p .github/workflows
   cp .github_workflows_ai_trends.yml .github/workflows/ai_trends.yml
   git add .github/workflows/ai_trends.yml
   git commit -m "Add AI trends automation"
   git push
   ```

5. **Test it:**
   - Go to GitHub → Actions tab
   - Click "AI Trends Weekly Update"
   - Click "Run workflow" → "Run workflow"
   - Wait 2 min, check if it succeeded
   - Netlify dashboard should show new deploy

6. **Done!**
   - Runs automatically every Sunday 6 PM UTC
   - Publish link: Share from Netlify dashboard

---

### Path C: AWS Lambda (45 min)
Best for: Serverless, no GitHub dependency

**Prerequisites:**
- AWS account
- S3 bucket for output

**Steps:**

1. **Create Lambda function:**
   - AWS Lambda → Create function
   - Runtime: Python 3.11
   - Handler: `lambda_function.lambda_handler`

2. **Add code:**
   ```python
   import json
   import os
   import sys
   sys.path.insert(0, '/var/task')
   import boto3
   from ai_trends_production import main

   s3 = boto3.client('s3')

   def lambda_handler(event, context):
       os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY')
       report = main()
       
       s3.put_object(
           Bucket=os.environ['BUCKET_NAME'],
           Key='ai_trends_report.json',
           Body=json.dumps(report),
           ContentType='application/json'
       )
       
       return {'statusCode': 200, 'body': json.dumps('Success')}
   ```

3. **Add environment:**
   - Lambda → Configuration → Environment variables
   - Add: `ANTHROPIC_API_KEY` and `BUCKET_NAME`

4. **Add schedule:**
   - Lambda → Add trigger
   - EventBridge (CloudWatch Events)
   - Rule: `cron(0 18 * * ? *)` (Sunday 6 PM UTC)
   - Target: This Lambda

5. **Create deployment package:**
   ```bash
   pip install -r requirements.txt -t ./package
   cp ai_trends_production.py package/
   cd package && zip -r ../lambda.zip . && cd ..
   ```

6. **Upload:**
   - Lambda → Upload from .zip file
   - Select lambda.zip

---

## Manual Option (No Automation)

If you don't want to set up scheduling, just run manually:

```bash
# Whenever you want an update
python ai_trends_production.py

# Then publish to Netlify
netlify deploy --prod
```

Or keep it local and just open `dashboard.html` whenever you want to check.

---

## What Each Option Costs

| Option | Setup Time | Weekly Cost | Effort to Maintain |
|--------|-----------|------------|-------------------|
| **Local** | 5 min | $0.02/week (if manual) | Manual run + upload |
| **GitHub+Netlify** | 1 hour | $0.02/week | None (fully automated) |
| **Lambda** | 45 min | $0.03/week | None (fully automated) |

---

## Next: Customization (Optional)

After you get it running, you can customize:

**Change what gets tracked:**
- Edit `SOURCES` in `ai_trends_production.py`
- Add your own RSS feeds

**Change scoring:**
- Adjust weights in `calculate_final_score()`
- Modify commercial keywords in `detect_commercial_intent()`

**Change schedule:**
- Update cron in workflow or Lambda trigger

See `SETUP.md` for details.

---

## Validation Checklist

Before considering it "done":

- [ ] Local test runs without errors (`python ai_trends_production.py`)
- [ ] `ai_trends_report.json` is generated
- [ ] `dashboard.html` loads and shows items
- [ ] Filters work (hide commercial, filter by category, etc.)
- [ ] Deployment chosen and secrets added (if automated)
- [ ] Manual workflow trigger works (if GitHub)
- [ ] Netlify or output shows updated date/time

---

## Support

**If something breaks:**

1. Check `.md` files for troubleshooting
2. Run locally to isolate the issue
3. Check GitHub Actions or Lambda logs
4. Verify API key is set: `echo $ANTHROPIC_API_KEY`

**If scoring seems off:**

1. Check individual item reasoning — explain why it scored as it did
2. After 2–3 weeks, adjust `cost_score`, `competitive_score`, `expectation_score` weights
3. Edit commercial keywords if false positives/negatives

---

## Questions?

- **What if RSS feeds are down?** — HN items still collected, lower total items that week
- **What if Claude API is slow?** — Lambda has 60-second timeout, should be enough
- **Can I add more sources?** — Yes, add to `SOURCES` dict in code
- **How often should I check it?** — Weekly auto-run, so every Monday morning
- **Can I run it daily instead of weekly?** — Yes, change cron to `cron(0 9 * * *)` or `0 18 * * 0 → 0 18 * * *`

---

## You're Ready!

Pick a path (Local → GitHub+Netlify → Lambda) and start with that.

**Recommended:** Path B (GitHub+Netlify) if you already have a GitHub repo. Otherwise Path A (local) to test first.

Let me know if you hit any blockers!
