from nba_api.stats.endpoints import leaguedashteamstats
from nba_api.stats.static import teams as static_teams
import pandas as pd


def update_team_data(season="2025-26"):
    """
    Pull pace- and opponent-adjusted TEAM stats and save them for ScoutIQ.

    These are the metrics that actually describe team quality. You cannot get
    them by summing individual box scores, which is why the old ratings were
    off (raw PPG rewards volume/pace, and player box scores can't measure team
    defense at all).
    """
    print("Downloading team advanced stats...")

    adv = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        measure_type_detailed_defense="Advanced",
    ).get_data_frames()[0]

    # Map TEAM_ID -> abbreviation so it matches the rest of the app.
    abbr = {t["id"]: t["abbreviation"] for t in static_teams.get_teams()}
    adv["TEAM_ABBREVIATION"] = adv["TEAM_ID"].map(abbr)

    cols = [
        "TEAM_ABBREVIATION", "TEAM_NAME", "GP",
        "OFF_RATING", "DEF_RATING", "NET_RATING",
        "AST_PCT", "OREB_PCT", "DREB_PCT", "REB_PCT",
        "EFG_PCT", "TS_PCT", "PACE",
    ]

    adv[cols].to_csv("data/processed/scoutiq_teams.csv", index=False)
    print(f"Saved advanced ratings for {len(adv)} teams.")


if __name__ == "__main__":
    update_team_data()