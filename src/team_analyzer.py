import os

import numpy as np
import pandas as pd

PLAYER_CSV = "data/processed/scoutiq_master.csv"
TEAM_CSV = "data/processed/scoutiq_teams.csv"

# ===========================================================================
# PLAYER DATA  (used for the roster view and per-player ratings)
# ===========================================================================

df = pd.read_csv(PLAYER_CSV)
df = df[df["GP"] >= 10].copy()


def _per_game(total_col, new_col):
    if new_col not in df.columns and total_col in df.columns:
        df[new_col] = df[total_col] / df["GP"]


for _t, _n in [
    ("PTS", "PTS_PER_GAME"), ("REB", "REB_PER_GAME"), ("AST", "AST_PER_GAME"),
    ("STL", "STL_PER_GAME"), ("BLK", "BLK_PER_GAME"), ("TOV", "TOV_PER_GAME"),
    ("DREB", "DREB_PER_GAME"),
]:
    _per_game(_t, _n)

df["MIN_PER_GAME"] = df["MIN"] / df["GP"]

df["SCORING_RAW"] = df["PTS_PER_GAME"]
df["SHOOTING_RAW"] = 0.5 * df["FG3_PCT"] + 0.3 * df["FG_PCT"] + 0.2 * df["FT_PCT"]
df["PLAYMAKING_RAW"] = df["AST_PER_GAME"] - 0.3 * df["TOV_PER_GAME"]
df["REBOUNDING_RAW"] = df["REB_PER_GAME"]
df["DEFENSE_RAW"] = (
    0.45 * df["STL_PER_GAME"] + 0.35 * df["BLK_PER_GAME"] + 0.20 * df["DREB_PER_GAME"]
)

PLAYER_RAW = {
    "Scoring": "SCORING_RAW", "Shooting": "SHOOTING_RAW",
    "Playmaking": "PLAYMAKING_RAW", "Rebounding": "REBOUNDING_RAW",
    "Defense": "DEFENSE_RAW",
}
for _c in PLAYER_RAW.values():
    df[_c] = df[_c].fillna(0)

_ROTATION = df[df["MIN_PER_GAME"] >= 10]
for _label, _col in PLAYER_RAW.items():
    df[_label + "_RATING"] = (
        (_ROTATION[_col].rank(pct=True) * 9 + 1).round(1).reindex(df.index)
    )


def get_player_ratings(player_name):
    player = df[df["PLAYER_NAME"] == player_name]
    if player.empty:
        return None
    player = player.iloc[0]
    out = {}
    for label in PLAYER_RAW:
        val = player[label + "_RATING"]
        out[label] = None if pd.isna(val) else round(float(val), 1)
    return out


def get_team_players(team, n=10):
    roster = df[df["TEAM_ABBREVIATION"] == team]
    return roster.sort_values("MIN", ascending=False).head(n)


# ===========================================================================
# TEAM RATINGS
# ===========================================================================
#   Scoring    -> OFF_RATING   (points scored per 100 possessions)
#   Shooting   -> TS_PCT       (true shooting %, includes 3s and FTs)
#   Playmaking -> AST_PCT      (share of made baskets that were assisted)
#   Rebounding -> REB_PCT      (share of available rebounds grabbed)
#   Defense    -> DEF_RATING   (points ALLOWED per 100 poss; lower is better)

TEAM_SOURCE = {
    "Scoring": ("OFF_RATING", True),
    "Shooting": ("TS_PCT", True),
    "Playmaking": ("AST_PCT", True),
    "Rebounding": ("REB_PCT", True),
    "Defense": ("DEF_RATING", False),
}


def _rank_1_10(series, higher_is_better=True):
    return (series.rank(pct=True, ascending=higher_is_better) * 9 + 1).round(1)


def _team_ratings_from_advanced():
    teams = pd.read_csv(TEAM_CSV)
    teams = teams.dropna(subset=["TEAM_ABBREVIATION"]).set_index("TEAM_ABBREVIATION")
    rated = pd.DataFrame(index=teams.index)
    for metric, (col, higher) in TEAM_SOURCE.items():
        rated[metric] = _rank_1_10(teams[col], higher)
    return rated


def _team_ratings_from_players():
    d = df.copy()
    if "OREB" not in d.columns:
        d["OREB"] = (d["REB"] - d["DREB"]).clip(lower=0)

    agg = d.groupby("TEAM_ABBREVIATION")[
        ["PTS", "FGA", "FGM", "FTA", "AST", "REB", "DREB", "OREB",
         "STL", "BLK", "TOV", "MIN"]
    ].sum()

    games = (agg["MIN"] / 240.0).clip(lower=1)
    poss = (agg["FGA"] + 0.44 * agg["FTA"] + agg["TOV"] - agg["OREB"]).clip(lower=1)

    raw = pd.DataFrame(index=agg.index)
    raw["Scoring"] = 100 * agg["PTS"] / poss
    raw["Shooting"] = agg["PTS"] / (2 * (agg["FGA"] + 0.44 * agg["FTA"]))
    raw["Playmaking"] = agg["AST"] / agg["FGM"].clip(lower=1)
    raw["Rebounding"] = agg["REB"] / games
    raw["Defense"] = (agg["STL"] + agg["BLK"]) / games + 0.5 * agg["DREB"] / games

    rated = pd.DataFrame(index=raw.index)
    for metric in TEAM_SOURCE:
        rated[metric] = _rank_1_10(raw[metric], True)
    return rated


if os.path.exists(TEAM_CSV):
    _TEAM_RATINGS = _team_ratings_from_advanced()
    RATING_SOURCE = "advanced"
else:
    _TEAM_RATINGS = _team_ratings_from_players()
    RATING_SOURCE = "player-box-fallback"


def get_team_names():
    if _TEAM_RATINGS is not None and len(_TEAM_RATINGS):
        return sorted(_TEAM_RATINGS.index)
    return sorted(df["TEAM_ABBREVIATION"].dropna().unique())


def get_team_ratings(team):
    if team not in _TEAM_RATINGS.index:
        return None
    return {k: float(v) for k, v in _TEAM_RATINGS.loc[team].items()}


def get_team_strengths(team):
    ratings = get_team_ratings(team)
    if ratings is None:
        return []
    return sorted(ratings.items(), key=lambda x: x[1], reverse=True)


NEED_LABELS = {
    "Scoring": "More Scoring",
    "Shooting": "More Shooting",
    "Playmaking": "Secondary Playmaker",
    "Rebounding": "Interior Rebounding",
    "Defense": "Defense",
}
NEED_THRESHOLD = 4.5


def get_team_needs(team):
    ratings = get_team_ratings(team)
    if ratings is None:
        return ["Team not found"]
    needs = [label for key, label in NEED_LABELS.items() if ratings[key] < NEED_THRESHOLD]
    if not needs:
        needs.append("No major weaknesses")
    return needs


CATEGORIES = list(TEAM_SOURCE.keys())


def get_team_rank(team):
    """Return {category: (rank, total_teams)} where rank 1 = best in league."""
    if team not in _TEAM_RATINGS.index:
        return None
    total = len(_TEAM_RATINGS)
    out = {}
    for c in TEAM_SOURCE:
        order = _TEAM_RATINGS[c].rank(ascending=False, method="min")
        out[c] = (int(order.loc[team]), total)
    return out


if __name__ == "__main__":
    print("Rating source:", RATING_SOURCE)
    for t in get_team_names():
        print(t, get_team_ratings(t))