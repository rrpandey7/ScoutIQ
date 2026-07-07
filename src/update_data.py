from nba_api.stats.endpoints import leaguedashplayerstats
import pandas as pd

import re
import unicodedata


def clean_name(name):
    """
    Standardize player names so different data sources match.
    """

    # Remove accents
    name = unicodedata.normalize("NFKD", str(name))
    name = name.encode("ascii", "ignore").decode("utf-8")

    # Remove periods
    name = name.replace(".", "")

    # Remove suffixes
    name = re.sub(r"\b(Jr|Sr|II|III|IV)\b", "", name)

    # Remove extra spaces
    aliases = {
    "adama bal": "adama-alpha bal",
    "egor demin": "egor demin",
    "ronald holland": "ron holland",
    "trevon scott": "tre scott"
}

    name = aliases.get(name.lower(), name.lower())

    return name

def percentile_rating(series):
    """
    Converts a statistic into a 1–10 rating using percentiles.
    """
    return (
        series.rank(pct=True) * 9 + 1
    ).round(1)


def update_data(season="2025-26"):

    print("Downloading NBA player stats...")

    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season
    )

    stats_df = stats.get_data_frames()[0]

    stats_df.to_csv(
        "data/raw/player_stats.csv",
        index=False
    )

    print("Loading player metadata...")

    metadata_df = pd.read_csv(
        "data/raw/player_metadata.csv"
    )

    # --------------------------
    # Remove duplicate players
    # --------------------------

    multi_team = metadata_df[
        metadata_df["Team"].isin(["2TM", "3TM"])
    ]

    covered = set(multi_team["Player"])

    single_team = metadata_df[
        ~metadata_df["Player"].isin(covered)
    ]

    metadata_df = pd.concat(
        [multi_team, single_team],
        ignore_index=True
    )
    stats_df["merge_name"] = stats_df["PLAYER_NAME"].apply(clean_name)

    metadata_df["merge_name"] = metadata_df["Player"].apply(clean_name)

    # Rename position column
    metadata_df = metadata_df.rename(
        columns={
            "Pos": "POSITION"
        }
    )

    # Merge metadata into NBA stats
    master_df = stats_df.merge(
        metadata_df[
            [
                "merge_name",
                "POSITION"
            ]
        ],
        on="merge_name",
        how="left"
    )
        # ----------------------------------
    # Create Per Game Stats
    # ----------------------------------

    master_df["PTS_PER_GAME"] = master_df["PTS"] / master_df["GP"]
    master_df["REB_PER_GAME"] = master_df["REB"] / master_df["GP"]
    master_df["AST_PER_GAME"] = master_df["AST"] / master_df["GP"]
    master_df["STL_PER_GAME"] = master_df["STL"] / master_df["GP"]
    master_df["BLK_PER_GAME"] = master_df["BLK"] / master_df["GP"]
    master_df["TOV_PER_GAME"] = master_df["TOV"] / master_df["GP"]

    # ----------------------------------
    # ScoutIQ Ratings
    # ----------------------------------

    master_df["SCORING_SCORE"] = percentile_rating(
        master_df["PTS_PER_GAME"]
    )

    master_df["SHOOTING_SCORE"] = percentile_rating(
        (
            master_df["FG3_PCT"] * 0.5 +
            master_df["FG_PCT"] * 0.3 +
            master_df["FT_PCT"] * 0.2
        )
    )

    playmaking_metric = (
        master_df["AST_PER_GAME"] -
        master_df["TOV_PER_GAME"] * 0.3
    )

    master_df["PLAYMAKING_SCORE"] = percentile_rating(
        playmaking_metric
    )

    master_df["REBOUNDING_SCORE"] = percentile_rating(
        master_df["REB_PER_GAME"]
    )

    defense_metric = (
        master_df["STL_PER_GAME"] * 0.45 +
        master_df["BLK_PER_GAME"] * 0.35 +
        master_df["DREB"] * 0.20
    )

    master_df["DEFENSE_SCORE"] = percentile_rating(
        defense_metric
    )

    # Remove helper column
    master_df = master_df.drop(
        columns=["merge_name"]
    )

    # Save master dataset
    master_df.to_csv(
        "data/processed/scoutiq_master.csv",
        index=False
    )

    print("\nPlayers missing positions:")

    print(
        master_df[
            master_df["POSITION"].isna()
        ][
            ["PLAYER_NAME"]
        ]
    )

if __name__ == "__main__":
    update_data()