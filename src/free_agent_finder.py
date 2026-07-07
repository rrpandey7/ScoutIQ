import pandas as pd

try:
    from src.team_analyzer import df, CATEGORIES
except ImportError:
    from team_analyzer import df, CATEGORIES


def _load_salaries(path="data/raw/player_salaries.csv"):
    try:
        s = pd.read_csv(path)
    except Exception:
        return None
    # Same two-row-header quirk the salary export uses.
    s.columns = s.iloc[0]
    s = s.iloc[1:]
    s = s.rename(columns={"Player": "PLAYER_NAME", "2025-26": "SALARY"})
    if "PLAYER_NAME" not in s.columns or "SALARY" not in s.columns:
        return None
    s = s[["PLAYER_NAME", "SALARY"]].copy()
    s["SALARY"] = (
        s["SALARY"].astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    s["SALARY"] = pd.to_numeric(s["SALARY"], errors="coerce")
    return s.dropna(subset=["SALARY"]).drop_duplicates("PLAYER_NAME")


_sal = _load_salaries()
_base = df.copy()
if _sal is not None:
    _base = _base.merge(_sal, on="PLAYER_NAME", how="left")
else:
    _base["SALARY"] = float("nan")

SALARY_AVAILABLE = _sal is not None


def find_free_agents(need, max_salary=None, max_age=None, top_n=10):
    """Rank players by the chosen skill rating, within salary and age limits."""
    if need not in CATEGORIES:
        return pd.DataFrame()

    col = need + "_RATING"
    d = _base.dropna(subset=[col]).copy()

    if max_salary is not None:
        # Keep unknown salaries in rather than silently dropping players.
        d = d[d["SALARY"].isna() | (d["SALARY"] <= max_salary)]
    if max_age is not None:
        d = d[d["AGE"] <= max_age]

    d = d.sort_values(col, ascending=False).head(top_n)

    out = d[["PLAYER_NAME", "TEAM_ABBREVIATION", "AGE", "SALARY", col]].copy()
    out = out.rename(columns={
        "PLAYER_NAME": "Player",
        "TEAM_ABBREVIATION": "Team",
        "AGE": "Age",
        "SALARY": "Salary",
        col: f"{need} Rating",
    })
    return out.reset_index(drop=True)


if __name__ == "__main__":
    print("Salaries loaded:", SALARY_AVAILABLE)
    print(find_free_agents("Shooting", max_salary=8_000_000, max_age=30))