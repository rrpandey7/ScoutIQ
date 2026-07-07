import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Load data
df = pd.read_csv("data/raw/player_stats.csv")

# Filter out players with low playing time
df = df[(df["MIN"] > 15) & (df["GP"] > 20)]

# Create per-game stats
df["PTS_PER_GAME"] = df["PTS"] / df["GP"]
df["REB_PER_GAME"] = df["REB"] / df["GP"]
df["AST_PER_GAME"] = df["AST"] / df["GP"]
df["STL_PER_GAME"] = df["STL"] / df["GP"]
df["BLK_PER_GAME"] = df["BLK"] / df["GP"]

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

scaler = StandardScaler()

scaled_stats = scaler.fit_transform(df[FEATURES])

similarity_matrix = cosine_similarity(scaled_stats)

print(f"Similarity Matrix Shape: {similarity_matrix.shape}")

def find_similar_players(player_name, top_n=5):

    matching_players = df[df["PLAYER_NAME"] == player_name]

    if matching_players.empty:
        print(f"Player '{player_name}' not found.")
        return

    player_idx = matching_players.index[0]

    similarity_scores = list(
        enumerate(
            similarity_matrix[
                df.index.get_loc(player_idx)
            ]
        )
    )

    similarity_scores = sorted(
        similarity_scores,
        key=lambda x: x[1],
        reverse=True
    )

    similarity_scores = similarity_scores[1:top_n+1]

    print(f"\nPlayers similar to {player_name}\n")

    for idx, score in similarity_scores:

        player = df.iloc[idx]

        print(
            f"{player['PLAYER_NAME']} "
            f"| Score: {score:.3f}"
        )

# Tests
find_similar_players("Aaron Gordon")
find_similar_players("Stephen Curry")
find_similar_players("Victor Wembanyama")
find_similar_players("Jalen Duren")