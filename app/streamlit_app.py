import streamlit as st
import plotly.graph_objects as go

from src.player_finder import (
    find_replacements,
    get_player_names,
    get_player_info,
    get_player_stats,
    generate_scouting_report,
    explain_recommendation,
)
from src.team_analyzer import (
    get_team_names,
    get_team_players,
    get_team_ratings,
    get_team_strengths,
    get_team_needs,
    get_team_rank,
    get_player_ratings,
    CATEGORIES,
)
from src.visualizations import (
    player_radar_chart,
    player_comparison_chart,
)
from src.trade_analyzer import (
    simulate_trade,
    list_team_players,
    get_all_players,
    team_profile,
)
from src.free_agent_finder import find_free_agents, SALARY_AVAILABLE
from src.gm_assistant import ask_gm
from src.team_analyzer import df as _player_df

st.set_page_config(page_title="ScoutIQ", page_icon="🏀", layout="wide")

import os

# Let the API key come from Streamlit secrets (works locally via
# .streamlit/secrets.toml and on Streamlit Cloud via the Secrets UI).
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass


def _salary_of(name):
    info = get_player_info(name)
    if info and info.get("salary"):
        return float(info["salary"])
    return 0.0


def _position_of(name):
    if "POSITION" not in _player_df.columns:
        return None
    match = _player_df[_player_df["PLAYER_NAME"] == name]
    if match.empty:
        return None
    val = match.iloc[0]["POSITION"]
    if val is None or val != val:  # NaN check without importing pandas
        return None
    return str(val)


# ---------------------------------------------------------------------------
# Shared visual helpers
# ---------------------------------------------------------------------------

def rating_color(value):
    if value >= 7:
        return "#22c55e"
    if value >= 4.5:
        return "#f59e0b"
    return "#ef4444"


def rating_bar(label, value, rank=None):
    pct = max(0, min(100, value * 10))
    color = rating_color(value)
    rank_txt = ""
    if rank is not None:
        rank_txt = f"<span style='color:#6b7280'>#{rank[0]} of {rank[1]}</span>"
    st.markdown(
        f"""
        <div style="margin:6px 0">
          <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:2px">
            <span><b>{label}</b></span>
            <span>{value}/10&nbsp;&nbsp;{rank_txt}</span>
          </div>
          <div style="background:#e5e7eb;border-radius:6px;height:10px;width:100%">
            <div style="width:{pct}%;background:{color};height:10px;border-radius:6px"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def radar_chart(profiles, names, title=""):
    fig = go.Figure()
    for prof, name in zip(profiles, names):
        r = [prof[c] for c in CATEGORIES] + [prof[CATEGORIES[0]]]
        theta = CATEGORIES + [CATEGORIES[0]]
        fig.add_trace(go.Scatterpolar(r=r, theta=theta, fill="toself", name=name))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 10], visible=True)),
        showlegend=len(names) > 1,
        height=380,
        margin=dict(l=50, r=50, t=50, b=30),
        title=title,
    )
    return fig


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

st.sidebar.title("🏀 ScoutIQ")
page = st.sidebar.radio(
    "Navigation",
    [
        "🔍 Player Explorer",
        "📊 Team Dashboard",
        "🔄 Trade Analyzer",
        "🧳 Free Agent Finder",
        "🤖 GM Assistant",
    ],
)


# ===========================================================================
# PLAYER EXPLORER
# ===========================================================================
if page == "🔍 Player Explorer":
    st.title("ScoutIQ 🏀")
    st.subheader("NBA Player Replacement & Scouting Tool")
    st.caption(
        "Identify statistically similar NBA players, compare performance, "
        "and generate scouting reports using machine learning."
    )
    st.divider()

    player_name = st.selectbox("Player", get_player_names())
    player_info = get_player_info(player_name)
    player_stats = get_player_stats(player_name)
    ratings = get_player_ratings(player_name)

    left, right = st.columns([2, 1])

    # ---- Right: player identity card ----
    with right:
        st.subheader(f"👤 {player_name}")
        if player_info:
            st.metric("Team", player_info["team"])
            st.metric("Age", int(player_info["age"]))
            st.metric("Salary", f"${player_info['salary']:,.0f}")
        pos = _position_of(player_name)
        if pos:
            st.metric("Position", pos)

        if ratings and any(v is not None for v in ratings.values()):
            safe = {k: (v if v is not None else 0.0) for k, v in ratings.items()}
            st.plotly_chart(
                player_radar_chart(safe, player_name),
                use_container_width=True,
            )
            st.markdown("**ScoutIQ Ratings**")
            for metric in CATEGORIES:
                rating_bar(metric, safe[metric])
        else:
            st.caption("Not enough minutes for a ScoutIQ profile.")

    # ---- Left: stats + scouting report ----
    with left:
        if player_stats:
            st.subheader("📈 Player Statistics")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PPG", player_stats["PTS"])
            c2.metric("RPG", player_stats["REB"])
            c3.metric("APG", player_stats["AST"])
            c4.metric("3PT%", f"{player_stats['FG3_PCT']}%")

        st.subheader("📝 Scouting Report")
        if st.button("Generate Scouting Report"):
            report = generate_scouting_report(player_name)
            if report:
                st.markdown("### Summary")
                st.write(report["summary"])
                st.markdown("### Strengths")
                for s in report["strengths"]:
                    st.write(f"✅ {s}")
                st.markdown("### Areas for Improvement")
                for w in report["weaknesses"]:
                    st.write(f"⚠️ {w}")
                st.markdown("### Ideal Role")
                st.success(report["role"])

    st.divider()

    max_salary = st.sidebar.slider(
        "Maximum Salary", 1_000_000, 60_000_000, 25_000_000, 1_000_000
    )
    st.sidebar.caption(f"💰 Maximum Salary: **${max_salary:,.0f}**")
    max_age = st.sidebar.slider("Maximum Age", 18, 40, 30)

    if st.sidebar.button("🔍 Find Replacements"):
        results = find_replacements(player_name, max_salary=max_salary, max_age=max_age)
        if len(results) == 0:
            st.error("No players found.")
        else:
            results["Similarity %"] = (
                results["Similarity"] * 100
            ).round(1).astype(str) + "%"
            top = results.iloc[0]
            st.success(f"🏆 Best Match: {top['Player']} ({top['Similarity %']} Similarity)")

            explanation, comparison_df = explain_recommendation(player_name, top["Player"])
            st.markdown("💡 Why this recommendation?")
            st.info(explanation)
            st.markdown("📊 Player Comparison")
            st.dataframe(comparison_df, hide_index=True, use_container_width=True)

            # Salary would dwarf every other bar, so chart the on-court metrics only.
            chart_df = comparison_df[~comparison_df["Metric"].isin(["Salary"])]
            st.plotly_chart(
                player_comparison_chart(chart_df),
                use_container_width=True,
            )

            alt = results.iloc[1:].copy()
            alt["Salary"] = alt["Salary"].apply(lambda x: f"${x:,.0f}")
            alt = alt.drop(columns=["Similarity"])
            st.markdown("🎯 Alternative Replacement Options")
            st.dataframe(alt, hide_index=True, use_container_width=True)


# ===========================================================================
# TEAM DASHBOARD
# ===========================================================================
elif page == "📊 Team Dashboard":
    st.title("📊 Team Dashboard")
    team = st.selectbox("Select Team", get_team_names())

    ratings = get_team_ratings(team)
    ranks = get_team_rank(team)
    roster = get_team_players(team)

    if ratings is None:
        st.error("No ratings available for this team.")
    else:
        avg_age = float(roster["AGE"].mean()) if "AGE" in roster.columns else None
        total_salary = 0.0
        have_salary = False
        for name in roster["PLAYER_NAME"]:
            info = get_player_info(name)
            if info and info.get("salary"):
                total_salary += float(info["salary"])
                have_salary = True

        m1, m2, m3 = st.columns(3)
        m1.metric("Roster Size", len(roster))
        if avg_age is not None:
            m2.metric("Average Age", f"{avg_age:.1f}")
        if have_salary:
            m3.metric("Rotation Salary", f"${total_salary:,.0f}")

        st.divider()
        left, right = st.columns([1, 1])

        with left:
            st.subheader("Team Ratings")
            for c in CATEGORIES:
                rating_bar(c, ratings[c], ranks[c] if ranks else None)

        with right:
            st.subheader("Profile")
            st.plotly_chart(radar_chart([ratings], [team]), use_container_width=True)

        st.divider()
        s1, s2 = st.columns(2)
        with s1:
            st.subheader("💪 Strengths")
            for skill, score in get_team_strengths(team)[:2]:
                st.markdown(
                    f"<span style='color:#22c55e'>⭐ **{skill}** — {score}/10</span>",
                    unsafe_allow_html=True,
                )
        with s2:
            st.subheader("🕳️ Weaknesses")
            for need in get_team_needs(team):
                st.markdown(
                    f"<span style='color:#ef4444'>⚠️ {need}</span>",
                    unsafe_allow_html=True,
                )

        st.divider()
        st.subheader("Roster")
        cols = ["PLAYER_NAME", "AGE", "MIN_PER_GAME",
                "PTS_PER_GAME", "REB_PER_GAME", "AST_PER_GAME"]
        cols = [c for c in cols if c in roster.columns]
        table = roster[cols].round(1).rename(columns={
            "PLAYER_NAME": "Player", "AGE": "Age", "MIN_PER_GAME": "MPG",
            "PTS_PER_GAME": "PPG", "REB_PER_GAME": "RPG", "AST_PER_GAME": "APG",
        })
        st.dataframe(table, hide_index=True, use_container_width=True)


# ===========================================================================
# TRADE ANALYZER
# ===========================================================================
elif page == "🔄 Trade Analyzer":
    st.title("🔄 Trade Analyzer")
    st.caption("Build a multi-player deal (picks optional) and see how it reshapes your team.")
    st.caption("Pick format: comma-separated, e.g. `2027 1st, 2028 2nd (via MIA)`. Leave blank for none.")

    team = st.selectbox("Team", get_team_names())
    mine = list_team_players(team)
    candidates = [p for p in get_all_players() if p not in mine]

    c1, c2 = st.columns(2)
    with c1:
        send = st.multiselect("Trade Away (players)", mine)
        send_picks_raw = st.text_input(
            "Picks you send (comma-separated)", "",
            placeholder="2027 1st, 2028 2nd (via MIA)",
        )
    with c2:
        receive = st.multiselect("Receive (players)", candidates)
        receive_picks_raw = st.text_input(
            "Picks you receive (comma-separated)", "",
            placeholder="2026 1st, 2029 2nd",
        )

    send_picks = [p.strip() for p in send_picks_raw.split(",") if p.strip()]
    receive_picks = [p.strip() for p in receive_picks_raw.split(",") if p.strip()]

    if st.button("Analyze Trade"):
        result = simulate_trade(team, send, receive, send_picks, receive_picks)
        if result is None:
            st.error("Add at least one player or pick to analyze.")
        else:
            st.subheader("Results")
            cols = st.columns(len(CATEGORIES))
            for col, cat in zip(cols, CATEGORIES):
                d = result["deltas"][cat]
                col.metric(cat, result["after"][cat], f"{d:+.1f}")

            fit = result["fit"]
            fit_color = "#22c55e" if fit >= 70 else "#f59e0b" if fit >= 50 else "#ef4444"
            st.markdown(
                f"<h3>Overall Fit: <span style='color:{fit_color}'>{fit}/100</span> "
                f"<span style='font-size:14px;color:#6b7280'>(on-court, this season)</span></h3>",
                unsafe_allow_html=True,
            )

            p1, p2 = st.columns(2)
            with p1:
                for pro in result["pros"]:
                    st.markdown(f"✅ {pro}")
            with p2:
                for con in result["cons"]:
                    st.markdown(f"❌ {con}")

            # Salary ledger
            out_sal = sum(_salary_of(p) for p in result["send"])
            in_sal = sum(_salary_of(p) for p in result["receive"])
            if out_sal or in_sal:
                s1, s2, s3 = st.columns(3)
                s1.metric("Salary Out", f"${out_sal:,.0f}")
                s2.metric("Salary In", f"${in_sal:,.0f}")
                s3.metric("Net", f"${in_sal - out_sal:,.0f}")

            # Draft picks (future assets, no rating impact)
            if result["send_picks"] or result["receive_picks"]:
                st.markdown("**Draft picks** (future value, not counted in ratings)")
                k1, k2 = st.columns(2)
                with k1:
                    for pk in result["receive_picks"]:
                        st.markdown(f"📥 {pk}")
                with k2:
                    for pk in result["send_picks"]:
                        st.markdown(f"📤 {pk}")

            st.divider()
            title_bits = []
            if result["send"]:
                title_bits.append(", ".join(result["send"]))
            if result["receive"]:
                title_bits.append(", ".join(result["receive"]))
            st.plotly_chart(
                radar_chart(
                    [result["before"], result["after"]],
                    ["Before", "After"],
                    title=f"{team}: " + " → ".join(title_bits) if title_bits else team,
                ),
                use_container_width=True,
            )


# ===========================================================================
# FREE AGENT FINDER
# ===========================================================================
elif page == "🧳 Free Agent Finder":
    st.title("🧳 Free Agent Finder")
    st.caption("Find the best-available players for a specific team need.")

    if not SALARY_AVAILABLE:
        st.warning("Salary data not loaded — budget filter is disabled.")

    c1, c2, c3 = st.columns(3)
    with c1:
        need = st.selectbox("Need", CATEGORIES)
    with c2:
        budget = st.slider("Budget", 1_000_000, 60_000_000, 8_000_000, 1_000_000)
    with c3:
        max_age = st.slider("Max Age", 18, 40, 30)

    if st.button("Find Players"):
        results = find_free_agents(
            need,
            max_salary=budget if SALARY_AVAILABLE else None,
            max_age=max_age,
        )
        if results.empty:
            st.error("No players match those filters.")
        else:
            if "Salary" in results.columns:
                results["Salary"] = results["Salary"].apply(
                    lambda x: f"${x:,.0f}" if x == x else "—"
                )
            st.dataframe(results, hide_index=True, use_container_width=True)


# ===========================================================================
# GM ASSISTANT
# ===========================================================================
elif page == "🤖 GM Assistant":
    st.title("🤖 Ask ScoutIQ")
    st.caption("Ask about any team's weaknesses and who to target. No setup required.")

    question = st.text_input(
        "Your question",
        placeholder="How can the Knicks improve their shooting?",
    )
    st.caption("Try: *What are the Timberwolves' weaknesses?* · *How do I fix Utah's defense?*")
    if st.button("Ask") and question:
        st.markdown(ask_gm(question))