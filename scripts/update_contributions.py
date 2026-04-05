#!/usr/bin/env python3
"""Fetch contribution data from GitHub API and update index.html."""
import subprocess, json, re
from datetime import datetime, timedelta

OWNER = "drkaushiksarkar"

def fetch_year(year):
    from_date = f"{year}-01-01T00:00:00Z"
    to_date = f"{year}-12-31T23:59:59Z"
    now = datetime.utcnow()
    if year == now.year:
        to_date = now.strftime("%Y-%m-%dT23:59:59Z")
    query = f"""query {{
      user(login: \"{OWNER}\") {{
        contributionsCollection(from: \"{from_date}\", to: \"{to_date}\") {{
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          totalRepositoryContributions
          contributionCalendar {{
            totalContributions
            weeks {{
              contributionDays {{ date contributionCount }}
            }}
          }}
        }}
      }}
    }}"""
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return None
    data = json.loads(r.stdout)
    cc = data["data"]["user"]["contributionsCollection"]
    result = {
        "year": year,
        "total": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "issues": cc["totalIssueContributions"],
        "prs": cc["totalPullRequestContributions"],
    }
    if year >= datetime.utcnow().year - 1:
        days = []
        for week in cc["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days.append({"date": day["date"], "count": day["contributionCount"]})
        result["daily"] = days
    return result

yearly = []
all_daily = []
for year in range(2009, datetime.utcnow().year + 1):
    result = fetch_year(year)
    if result:
        yearly.append(result)
        if "daily" in result:
            all_daily.extend(result["daily"])
        print(f"  {year}: {result['total']}")

cutoff = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
last_month = [d for d in all_daily if d["date"] >= cutoff]

# Update index.html
with open("index.html") as f:
    html = f.read()

yearly_clean = [{"year": y["year"], "total": y["total"], "commits": y["commits"],
                 "issues": y["issues"], "prs": y["prs"]} for y in yearly]

html = re.sub(r"const yearlyData = .*?;", f"const yearlyData = {json.dumps(yearly_clean)};", html)
html = re.sub(r"const monthlyData = .*?;", f"const monthlyData = {json.dumps(last_month)};", html)

with open("index.html", "w") as f:
    f.write(html)

print(f"Updated: {len(yearly)} years, {len(last_month)} days last month")