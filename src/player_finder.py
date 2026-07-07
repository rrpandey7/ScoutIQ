import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# -------------------
# LOAD PLAYER STATS
# -------------------

df = pd.read_csv("data/processed/scoutiq_master.csv")

df = df[(df["MIN"] > 15) & (df["GP"] > 10)]



# -------------------
# LOAD SALARIES
# -------------------

salary_df = pd.read_csv("data/raw/player_salaries.csv")

salary_df.columns = salary_df.iloc[0]
salary_df = salary_df.iloc[1:]

salary_df = salary_df.rename(
    columns={
        "Player": "PLAYER_NAME",
        "2025-26": "SALARY"
    }
)

salary_df = salary_df[
    ["PLAYER_NAME", "SALARY"]
]

salary_df["SALARY"] = (
    salary_df["SALARY"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

salary_df["SALARY"] = pd.to_numeric(
    salary_df["SALARY"],
    errors="coerce"
)

salary_df = salary_df.dropna(subset=["SALARY"])

salary_df = salary_df.drop_duplicates(
    subset=["PLAYER_NAME"]
)

# -------------------
# MERGE
# -------------------

df = pd.merge(
    df,
    salary_df,
    on="PLAYER_NAME",
    how="inner"
)

# -------------------
# FEATURES
# -------------------

FEATURES = [
    "PTS_PER_GAME",
    "REB_PER_GAME",
    "AST_PER_GAME",
    "STL_PER_GAME",
    "BLK_PER_GAME",
    "FG_PCT",
    "FG3_PCT",
    "FT_PCT"
]

df = df.dropna(subset=FEATURES)

# -------------------
# SIMILARITY MODEL
# -------------------

scaler = StandardScaler()

scaled_stats = scaler.fit_transform(
    df[FEATURES]
)

similarity_matrix = cosine_similarity(
    scaled_stats
)

# -------------------
# GM FUNCTIONS
# -------------------

def find_replacements(player_name, max_salary=None, max_age=None, top_n=10):

    matching_player = df[
        df["PLAYER_NAME"] == player_name
    ]

    if matching_player.empty:
        return pd.DataFrame()

    player_idx = matching_player.index[0]

    similarities = list(
        enumerate(
            similarity_matrix[
                df.index.get_loc(player_idx)
            ]
        )
    )

    similarities = sorted(
        similarities,
        key=lambda x: x[1],
        reverse=True
    )

    results = []

    for idx, score in similarities[1:]:

        player = df.iloc[idx]

        if max_salary is not None:
            if player["SALARY"] > max_salary:
                continue

        if max_age is not None:
            if player["AGE"] > max_age:
                continue

        results.append({
            "Player": player["PLAYER_NAME"],
            "Team": player["TEAM_ABBREVIATION"],
            "Age": player["AGE"],
            "Salary": player["SALARY"],
            "Similarity": round(score, 3)
        })

        if len(results) >= top_n:
            break

    return pd.DataFrame(results)

def get_player_names():
    return sorted(df["PLAYER_NAME"].unique())

def get_player_info(player_name):

    player = df[
        df["PLAYER_NAME"] == player_name
    ]

    if player.empty:
        return None

    player = player.iloc[0]

    return {
        "name": player["PLAYER_NAME"],
        "team": player["TEAM_ABBREVIATION"],
        "age": player["AGE"],
        "salary": player["SALARY"]
    }

def get_player_stats(player_name):

    player = df[
        df["PLAYER_NAME"] == player_name
    ]

    if player.empty:
        return None

    player = player.iloc[0]

    return {
        "PTS": round(player["PTS_PER_GAME"], 1),
        "REB": round(player["REB_PER_GAME"], 1),
        "AST": round(player["AST_PER_GAME"], 1),
        "FG3_PCT": round(player["FG3_PCT"] * 100, 1)
    }

def get_top_candidate(player_name):

    results = find_replacements(
        player_name,
        top_n=1
    )

    if len(results) == 0:
        return None

    return results.iloc[0]

def generate_scouting_report(player_name):

    info = get_player_info(player_name)
    stats = get_player_stats(player_name)

    if info is None or stats is None:
        return None

    strengths = []
    weaknesses = []

    # Strengths
    if stats["PTS"] >= 20:
        strengths.append("High-level scorer")

    if stats["REB"] >= 7:
        strengths.append("Strong rebounder")

    if stats["AST"] >= 5:
        strengths.append("Excellent playmaker")

    if stats["FG3_PCT"] >= 37:
        strengths.append("Reliable three-point shooter")

    # Weaknesses
    if stats["PTS"] < 15:
        weaknesses.append("Limited scoring production")

    if stats["REB"] < 5:
        weaknesses.append("Below-average rebounding")

    if stats["AST"] < 3:
        weaknesses.append("Limited playmaking")

    if stats["FG3_PCT"] < 33:
        weaknesses.append("Needs more consistent outside shooting")

    # Default values
    if len(strengths) == 0:
        strengths.append("Well-rounded contributor")

    if len(weaknesses) == 0:
        weaknesses.append("No major statistical weaknesses")

    # Role
    if stats["PTS"] >= 20:
        role = "Primary offensive option"

    elif stats["PTS"] >= 15:
        role = "Starting-caliber contributor"

    else:
        role = "Role player"

    summary = (
        f"{player_name} is a {int(info['age'])}-year-old player for "
        f"{info['team']} averaging "
        f"{stats['PTS']} PPG, "
        f"{stats['REB']} RPG and "
        f"{stats['AST']} APG."
    )

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "role": role
    }

def explain_recommendation(original_player, recommended_player):

    original = df[
        df["PLAYER_NAME"] == original_player
    ].iloc[0]

    replacement = df[
        df["PLAYER_NAME"] == recommended_player
    ].iloc[0]

    reasons = []

    if abs(
        original["PTS_PER_GAME"] -
        replacement["PTS_PER_GAME"]
    ) <= 3:
        reasons.append("similar scoring production")

    if abs(
        original["REB_PER_GAME"] -
        replacement["REB_PER_GAME"]
    ) <= 2:
        reasons.append("similar rebounding ability")

    if abs(
        original["AST_PER_GAME"] -
        replacement["AST_PER_GAME"]
    ) <= 2:
        reasons.append("similar playmaking")

    if abs(
        original["AGE"] -
        replacement["AGE"]
    ) <= 3:
        reasons.append("similar age")

    if len(reasons) == 0:
        reasons.append("an overall similar statistical profile")

    explanation = (
        f"{recommended_player} was identified as a strong replacement "
        f"because their statistical profile closely matches "
        f"{original_player}'s. "
        f"The comparison found {', '.join(reasons)}, while also "
        f"satisfying the selected salary and age constraints."
    )

    comparison = {
        "Metric": [
            "PPG",
            "RPG",
            "APG",
            "FG%",
            "3PT%",
            "STL",
            "BLK",
            "Age",
            "Salary"
        ],
        original_player: [
            round(original["PTS_PER_GAME"], 1),
            round(original["REB_PER_GAME"], 1),
            round(original["AST_PER_GAME"], 1),
            f"{round(original['FG_PCT'] * 100,1)}%",
            f"{round(original['FG3_PCT'] * 100,1)}%",
            round(original["STL_PER_GAME"], 1),
            round(original["BLK_PER_GAME"], 1),
            int(original["AGE"]),
            f"${original['SALARY']:,.0f}"
        ],
        recommended_player: [
            round(replacement["PTS_PER_GAME"], 1),
            round(replacement["REB_PER_GAME"], 1),
            round(replacement["AST_PER_GAME"], 1),
            f"{round(replacement['FG_PCT'] * 100,1)}%",
            f"{round(replacement['FG3_PCT'] * 100,1)}%",
            round(replacement["STL_PER_GAME"], 1),
            round(replacement["BLK_PER_GAME"], 1),
            int(replacement["AGE"]),
            f"${replacement['SALARY']:,.0f}"
        ]
    }


    comparison_df = pd.DataFrame(comparison)

    return explanation, comparison_df

def get_player_ratings(player_name):

    player = df[
        df["PLAYER_NAME"] == player_name
    ]

    if player.empty:
        return None

    player = player.iloc[0]

    return {
        "Scoring": round(player["SCORING_SCORE"], 1),
        "Shooting": round(player["SHOOTING_SCORE"], 1),
        "Playmaking": round(player["PLAYMAKING_SCORE"], 1),
        "Rebounding": round(player["REBOUNDING_SCORE"], 1),
        "Defense": round(player["DEFENSE_SCORE"], 1)
    }
# -------------------
# TESTS
# -------------------

if __name__ == "__main__":

    print(df.columns.tolist())