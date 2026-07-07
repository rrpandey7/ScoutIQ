"""
Keyless GM Assistant. Answers front-office questions directly from the ScoutIQ
ratings and the Free Agent Finder. No API key, no billing, no internet needed.
"""

try:
    from src.team_analyzer import (
        get_team_names, get_team_ratings, get_team_needs, get_team_rank, CATEGORIES,
    )
    from src.free_agent_finder import find_free_agents
except ImportError:
    from team_analyzer import (
        get_team_names, get_team_ratings, get_team_needs, get_team_rank, CATEGORIES,
    )
    from free_agent_finder import find_free_agents


# --- team name / nickname / city -> abbreviation ---------------------------
TEAM_ALIASES = {
    "ATL": ["atlanta", "hawks"], "BOS": ["boston", "celtics"],
    "BKN": ["brooklyn", "nets"], "CHA": ["charlotte", "hornets"],
    "CHI": ["chicago", "bulls"], "CLE": ["cleveland", "cavaliers", "cavs"],
    "DAL": ["dallas", "mavericks", "mavs"], "DEN": ["denver", "nuggets"],
    "DET": ["detroit", "pistons"], "GSW": ["golden state", "warriors"],
    "HOU": ["houston", "rockets"], "IND": ["indiana", "pacers"],
    "LAC": ["clippers"], "LAL": ["lakers"],
    "MEM": ["memphis", "grizzlies"], "MIA": ["miami", "heat"],
    "MIL": ["milwaukee", "bucks"], "MIN": ["minnesota", "timberwolves", "wolves"],
    "NOP": ["new orleans", "pelicans", "pels"], "NYK": ["new york", "knicks"],
    "OKC": ["oklahoma", "thunder"], "ORL": ["orlando", "magic"],
    "PHI": ["philadelphia", "sixers", "76ers"], "PHX": ["phoenix", "suns"],
    "POR": ["portland", "trail blazers", "blazers"], "SAC": ["sacramento", "kings"],
    "SAS": ["san antonio", "spurs"], "TOR": ["toronto", "raptors"],
    "UTA": ["utah", "jazz"], "WAS": ["washington", "wizards"],
}

CATEGORY_KEYWORDS = {
    "Scoring": ["scoring", "score", "offense", "offence", "points"],
    "Shooting": ["shooting", "shoot", "three", "3pt", "spacing", "shooter"],
    "Playmaking": ["playmaking", "passing", "assist", "point guard", "ball handler", "ball-handler"],
    "Rebounding": ["rebounding", "rebound", "boards", "glass"],
    "Defense": ["defense", "defence", "defensive", "stops", "guarding"],
}

ARCHETYPE = {
    "Scoring": "a high-usage shot creator",
    "Shooting": "a floor-spacing knockdown shooter",
    "Playmaking": "a secondary ball-handler / playmaker",
    "Rebounding": "a rebounding big",
    "Defense": "a rangy perimeter defender or rim protector",
}


def _match_team(text):
    text = text.lower()
    best, best_len = None, 0
    valid = set(get_team_names())
    for abbr, aliases in TEAM_ALIASES.items():
        if abbr not in valid:
            continue
        for alias in aliases + [abbr.lower()]:
            if alias in text and len(alias) > best_len:
                best, best_len = abbr, len(alias)
    return best


def _match_category(text):
    text = text.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cat
    return None


def _targets(category, exclude_team, n=3):
    fa = find_free_agents(category, max_salary=None, max_age=None, top_n=n + 6)
    if fa.empty:
        return []
    fa = fa[fa["Team"] != exclude_team]
    rating_col = f"{category} Rating"
    out = []
    for _, row in fa.head(n).iterrows():
        out.append(f"{row['Player']} ({row['Team']}, {row[rating_col]}/10)")
    return out


def _weakness_line(team, cat, ratings, ranks):
    rank, total = ranks[cat]
    return f"{cat}: #{rank} of {total} ({ratings[cat]}/10)"


def ask_gm(question):
    if not question or not question.strip():
        return "Ask me about a team, e.g. *How can the Knicks improve their shooting?*"

    team = _match_team(question)
    if team is None:
        names = ", ".join(sorted(get_team_names()))
        return (
            "I couldn't find a team in that question. Name one (city, nickname, or "
            f"abbreviation).\n\nTeams: {names}"
        )

    ratings = get_team_ratings(team)
    ranks = get_team_rank(team)
    needs = get_team_needs(team)
    category = _match_category(question)

    # Specific category asked about.
    if category:
        rank, total = ranks[category]
        rating = ratings[category]
        if rating >= 6.5:
            return (
                f"**{team}** is already a strength in {category}: "
                f"#{rank} of {total} ({rating}/10). I'd invest elsewhere — "
                f"their bigger needs are {', '.join(needs)}."
            )
        targets = _targets(category, team)
        lines = [
            f"**{team}** rank #{rank} of {total} in {category} ({rating}/10) — a real weakness.",
            f"Fix it by targeting {ARCHETYPE[category]}.",
        ]
        if targets:
            lines.append("Best available by " + category.lower() + " rating:")
            lines += [f"- {t}" for t in targets]
        return "\n\n".join(lines[:2]) + "\n\n" + "\n".join(lines[2:] if targets else [])

    # General "how do they improve" — rank the weaknesses.
    ranked = sorted(CATEGORIES, key=lambda c: ratings[c])
    weak = [c for c in ranked if ratings[c] < 6.5][:2] or ranked[:1]
    lines = [f"**{team}** rating profile: " + ", ".join(
        f"{c} {ratings[c]}" for c in CATEGORIES) + "."]
    lines.append("Biggest needs: " + ", ".join(_weakness_line(team, c, ratings, ranks) for c in weak) + ".")
    top = weak[0]
    targets = _targets(top, team)
    if targets:
        lines.append(f"Top priority is **{top}** — target {ARCHETYPE[top]}:")
        lines += [f"- {t}" for t in targets]
    return "\n\n".join(lines[:2]) + ("\n\n" + lines[2] + "\n" + "\n".join(f"- {t}" for t in targets) if targets else "")


if __name__ == "__main__":
    for q in [
        "How can BOS improve their shooting?",
        "What are the Timberwolves' weaknesses?",
        "How do I fix Utah's defense?",
    ]:
        print("Q:", q)
        print(ask_gm(q))
        print("-" * 60)