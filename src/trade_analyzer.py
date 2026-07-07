import numpy as np
import pandas as pd

try:
    from src.team_analyzer import (
        df, get_team_players, get_team_needs, CATEGORIES, NEED_LABELS,
    )
except ImportError:
    from team_analyzer import (
        df, get_team_players, get_team_needs, CATEGORIES, NEED_LABELS,
    )

# Neutral fill for players below the rotation cutoff (no rating).
_RATING_MEAN = {c: float(df[c + "_RATING"].mean()) for c in CATEGORIES}


def _profile(roster):
    """Minutes-weighted average of a roster's player ratings, per category."""
    if roster.empty:
        return {c: 0.0 for c in CATEGORIES}
    w = roster["MIN"].to_numpy(float)
    if not np.isfinite(w).all() or w.sum() <= 0:
        w = np.ones(len(roster))
    prof = {}
    for c in CATEGORIES:
        vals = roster[c + "_RATING"].fillna(_RATING_MEAN[c]).to_numpy(float)
        prof[c] = round(float(np.average(vals, weights=w)), 1)
    return prof


def team_profile(team):
    return _profile(get_team_players(team))


def list_team_players(team):
    roster = df[df["TEAM_ABBREVIATION"] == team].sort_values("MIN", ascending=False)
    return roster["PLAYER_NAME"].tolist()


def get_all_players():
    return sorted(df["PLAYER_NAME"].unique())


def _clean_list(items):
    return [x for x in (items or []) if x and str(x).strip()]


def simulate_trade(team, send, receive, send_picks=None, receive_picks=None):
    """
    Multi-player trade. `send` / `receive` are lists of player names.
    `send_picks` / `receive_picks` are lists of pick labels (strings).

    Players change the on-court profile (rotation recomputed, minutes-weighted).
    Draft picks are tracked as future assets: they are NOT current contributors,
    so they intentionally do NOT move the 1-10 ratings. They're reported
    separately so the deal ledger is honest.
    """
    send = _clean_list(send)
    receive = _clean_list(receive)
    send_picks = [str(p).strip() for p in _clean_list(send_picks)]
    receive_picks = [str(p).strip() for p in _clean_list(receive_picks)]

    if not (send or receive or send_picks or receive_picks):
        return None

    before = team_profile(team)

    remaining = df[
        (df["TEAM_ABBREVIATION"] == team) & (~df["PLAYER_NAME"].isin(send))
    ]
    incoming = df[df["PLAYER_NAME"].isin(receive)]
    new_roster = pd.concat([remaining, incoming], ignore_index=True)
    new_rotation = new_roster.sort_values("MIN", ascending=False).head(10)
    after = _profile(new_rotation)

    deltas = {c: round(after[c] - before[c], 1) for c in CATEGORIES}

    needs = set(get_team_needs(team))
    fit = 60.0
    for c, d in deltas.items():
        weight = 2.0 if NEED_LABELS[c] in needs else 1.0
        fit += d * 6.0 * weight
    fit = int(max(0, min(100, round(fit))))

    pros = [f"Better {c.lower()}" for c in CATEGORIES if deltas[c] >= 0.2]
    cons = [f"Worse {c.lower()}" for c in CATEGORIES if deltas[c] <= -0.2]

    return {
        "team": team,
        "send": send,
        "receive": receive,
        "send_picks": send_picks,
        "receive_picks": receive_picks,
        "before": before,
        "after": after,
        "deltas": deltas,
        "fit": fit,
        "pros": pros,
        "cons": cons,
    }


if __name__ == "__main__":
    try:
        from src.team_analyzer import get_team_names
    except ImportError:
        from team_analyzer import get_team_names
    t = get_team_names()[0]
    mine = list_team_players(t)
    others = [p for p in get_all_players() if p not in mine]
    r = simulate_trade(
        t, mine[:2], others[:1],
        send_picks=["2027 1st"], receive_picks=["2026 1st (via X)", "2028 2nd"],
    )
    print("send:", r["send"], "+ picks", r["send_picks"])
    print("recv:", r["receive"], "+ picks", r["receive_picks"])
    print("deltas:", r["deltas"], "fit:", r["fit"])