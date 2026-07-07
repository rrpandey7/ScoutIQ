ScoutIQ - NBA Player & Team Analytics Platform

ScoutIQ is a basketball analytics platform that turns raw NBA stats into front-office decisions. It scores players and teams, finds statistical replacements, simulates trades, and answers roster questions, all from real NBA data pulled through nba_api. It's built for the kind of work a scout or GM actually does: who's similar to this player, what does this team lack, and does this trade make us better.

Features

ScoutIQ provides a set of tools aimed at scouts, analysts, and basketball fans who want to reason about rosters with data:

Statistical Player Similarity: Finds the closest statistical matches to any player using a cosine-similarity model over standardized per-game stats, then filters the results by salary and age to surface realistic replacement targets.

ScoutIQ Rating Engine: Converts raw stats into 1-10 ratings across Scoring, Shooting, Playmaking, Rebounding, and Defense. Player ratings are percentiles within the rotation-player pool; team ratings are ranked against the rest of the league.

Advanced Team Analytics: Rates teams on pace- and opponent-adjusted advanced stats (offensive rating, true shooting %, assist %, rebound %, defensive rating) rather than raw box-score totals, so scoring reflects efficiency and defense reflects points allowed.

Trade Simulator: Builds multi-player deals with optional draft picks, recomputes the team's rotation profile, and returns per-category deltas, an Overall Fit score out of 100, a before/after radar, and a salary ledger.

Roster-Fit / Free Agent Finder: Ranks the best available players for a specific team need within a chosen budget and age limit.

GM Assistant: Answers natural-language questions like "How can the Timberwolves improve their rebounding?" with data-grounded responses and real target players. Runs entirely on local ratings, with no API key or billing required.

Automated Scouting Reports: Generates a summary, strengths, weaknesses, and an ideal role for any player from statistical thresholds.

Interactive Visualizations: Radar profiles, color-coded rating bars, grouped comparison charts, and salary/age distributions, all interactive via Plotly.

Data Pipeline: Scripts pull player and team stats from the NBA API, normalize player names across sources, derive per-game stats, and compute percentile-based ratings into clean processed datasets.

Tech Stack

App & UI


Streamlit (multi-page app with sidebar navigation)
Plotly (radar charts, bar charts, distributions)


Data & Machine Learning


Python
pandas (data wrangling and aggregation)
scikit-learn (StandardScaler + cosine similarity for the player-similarity model)
Percentile-based rating engine (players vs. rotation pool, teams vs. league)


Data Sources


nba_api (player box scores and team advanced stats from stats.nba.com)
Player salary and metadata CSVs


Project Structure

scoutiq/
├── app.py                       # Streamlit entry point and all page layouts
├── update_data.py               # Pulls player stats -> data/processed/scoutiq_master.csv
├── update_teams.py              # Pulls team advanced stats -> data/processed/scoutiq_teams.csv
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── player_salaries.csv  # Salary source (used by finder + comparisons)
│   │   └── player_metadata.csv  # Position metadata merged into the master set
│   └── processed/
│       ├── scoutiq_master.csv   # Cleaned per-game player stats + ratings
│       └── scoutiq_teams.csv    # Team advanced stats for league-wide ratings
└── src/
    ├── __init__.py
    ├── player_finder.py         # Similarity model, replacements, scouting reports, comparisons
    ├── team_analyzer.py         # Player + team ratings, league ranks, rosters
    ├── trade_analyzer.py        # Multi-player + pick trade simulation and fit scoring
    ├── free_agent_finder.py     # Need-based player search within budget and age
    ├── gm_assistant.py          # Keyless, data-grounded Q&A engine
    └── visualizations.py        # Plotly chart builders

Pages Overview

ScoutIQ presents its tools through a sidebar navigation with the following sections:

Player Explorer: Select any player to see a scouting card (team, age, salary, position), a ScoutIQ radar profile with rating bars, per-game statistics, and an auto-generated scouting report. Then find statistical replacements filtered by salary and age, with a side-by-side comparison table and chart.

Team Dashboard: Shows a team's league-wide ratings across the five categories with radar, colored bars, and rank (for example, #3 of 30 in Defense), alongside the roster, average age, and rotation salary.

Trade Analyzer: Build a multi-player deal (picks optional) and see how it reshapes the team. Returns category deltas, an Overall Fit score, a before/after radar, a salary ledger, and better/worse callouts.

Free Agent Finder: Choose a team need, a budget, and an age cap to get the best available players ranked by that skill.

GM Assistant: Ask front-office questions in plain language and get answers grounded in the team ratings, including specific players to target.