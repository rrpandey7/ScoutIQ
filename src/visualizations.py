import plotly.graph_objects as go
import plotly.express as px


# ==========================================
# PLAYER RADAR CHART
# ==========================================

def player_radar_chart(ratings, player_name):

    categories = [
        "Scoring",
        "Shooting",
        "Playmaking",
        "Rebounding",
        "Defense"
    ]

    values = [
        ratings["Scoring"],
        ratings["Shooting"],
        ratings["Playmaking"],
        ratings["Rebounding"],
        ratings["Defense"]
    ]

    values += values[:1]
    categories += categories[:1]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name=player_name,
            line=dict(width=3)
        )
    )

    fig.update_layout(

        title=f"{player_name} ScoutIQ Profile",

        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0,10]
            )
        ),

        showlegend=False,
        height=550
    )

    return fig


# ==========================================
# TEAM COMPARISON RADAR
# ==========================================

def compare_teams(team1, ratings1, team2, ratings2):

    categories = [
        "Scoring",
        "Shooting",
        "Playmaking",
        "Rebounding",
        "Defense"
    ]

    values1 = list(ratings1.values())
    values2 = list(ratings2.values())

    values1 += values1[:1]
    values2 += values2[:1]

    categories += categories[:1]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values1,
            theta=categories,
            fill="toself",
            name=team1
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=values2,
            theta=categories,
            fill="toself",
            name=team2
        )
    )

    fig.update_layout(

        title=f"{team1} vs {team2}",

        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0,10]
            )
        ),

        height=600
    )

    return fig


# ==========================================
# PLAYER COMPARISON BAR CHART
# ==========================================

def player_comparison_chart(comparison_df):

    players = comparison_df.columns[1:]

    fig = go.Figure()

    for player in players:

        values = []

        for value in comparison_df[player]:

            if isinstance(value, str):

                value = (
                    value
                    .replace("%","")
                    .replace("$","")
                    .replace(",","")
                )

            values.append(float(value))

        fig.add_trace(

            go.Bar(

                name=player,

                x=comparison_df["Metric"],

                y=values
            )
        )

    fig.update_layout(

        title="Player Comparison",

        barmode="group",

        height=550
    )

    return fig


# ==========================================
# SALARY DISTRIBUTION
# ==========================================

def salary_distribution(df):

    fig = px.histogram(

        df,

        x="SALARY",

        nbins=25,

        title="NBA Salary Distribution"
    )

    fig.update_layout(height=500)

    return fig


# ==========================================
# AGE DISTRIBUTION
# ==========================================

def age_distribution(df):

    fig = px.histogram(

        df,

        x="AGE",

        nbins=15,

        title="Player Age Distribution"
    )

    fig.update_layout(height=500)

    return fig


# ==========================================
# SCORING VS SHOOTING
# ==========================================

def scoring_vs_shooting(df):

    fig = px.scatter(

        df,

        x="PTS_PER_GAME",

        y="FG3_PCT",

        color="POSITION",

        hover_name="PLAYER_NAME",

        size="SALARY",

        title="Scoring vs Three Point Percentage"
    )

    fig.update_layout(height=650)

    return fig