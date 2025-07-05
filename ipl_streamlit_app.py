import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image

# Set up page
st.set_page_config(
    page_title="IPL Dashboard By Diya",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stSelectbox>div>div>select {
        background-color: #e8f5e9;
    }
    .css-1aumxhk {
        background-color: #e3f2fd;
    }
</style>
""", unsafe_allow_html=True)

# Load data with caching
@st.cache_data
def load_data():
    df = pd.read_csv("matches (1).csv")
    df['season'] = df['season'].replace({'2007/08': '2008', '2009/10': '2010', '2020/21': '2021'})
    return df

df = load_data()

# Sidebar filters (global)
st.sidebar.header("🔍 Global Filters")
all_seasons = sorted(df['season'].unique())
selected_seasons = st.sidebar.multiselect(
    "Select Seasons", 
    all_seasons, 
    default=all_seasons,
    key="season_filter"
)

all_teams = sorted(df['team1'].unique())
selected_teams = st.sidebar.multiselect(
    "Select Teams", 
    all_teams, 
    default=all_teams,
    key="team_filter"
)

venue_options = ['All'] + sorted(df['venue'].unique())
selected_venue = st.sidebar.selectbox(
    "Select Venue", 
    venue_options,
    key="venue_filter"
)

# Apply filters
filtered_df = df[df['season'].isin(selected_seasons) & 
                 (df['team1'].isin(selected_teams) | 
                  df['team2'].isin(selected_teams))]

if selected_venue != 'All':
    filtered_df = filtered_df[filtered_df['venue'] == selected_venue]

# Multi-page setup
page = st.sidebar.radio(
    "Navigate to:",
    ["📊 Overview", "🏆 Team Performance", "🎯 Match Analysis", "📈 Trends Over Time"],
    horizontal=True
)

# Page 1: Overview
if page == "📊 Overview":
    st.header("IPL Tournament Overview")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches", len(filtered_df))
    col2.metric("Teams Participating", len(set(filtered_df['team1']).union(set(filtered_df['team2']))))
    col3.metric("Venues Used", filtered_df['venue'].nunique())
    
    # Season timeline
    st.subheader("Season Timeline")
    fig = px.line(filtered_df['season'].value_counts().sort_index(), 
                 title="Matches per Season",
                 labels={'value': 'Number of Matches', 'index': 'Season'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Win/Loss pie
    st.subheader("Match Result Types")
    result_counts = filtered_df['result'].value_counts()
    fig = px.pie(result_counts, values=result_counts.values, 
                names=result_counts.index, hole=0.3)
    st.plotly_chart(fig, use_container_width=True)

# Page 2: Team Performance
elif page == "🏆 Team Performance":
    st.header("Team Performance Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Win Records", "Head-to-Head", "Venue Performance"])
    
    with tab1:
        st.subheader("Team Win Records")
        team_wins = filtered_df['winner'].value_counts().reset_index()
        team_wins.columns = ['Team', 'Wins']
        fig = px.bar(team_wins, x='Team', y='Wins', color='Wins',
                    title="Total Wins by Team")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Head-to-Head Performance")
        team1 = st.selectbox("Select Team 1", sorted(filtered_df['team1'].unique()))
        team2 = st.selectbox("Select Team 2", sorted(filtered_df['team1'].unique()))
        
        h2h = filtered_df[((filtered_df['team1'] == team1) & (filtered_df['team2'] == team2)) | 
               ((filtered_df['team1'] == team2) & (filtered_df['team2'] == team1))]
        
        if not h2h.empty:
            wins = h2h['winner'].value_counts()
            fig = px.pie(wins, values=wins.values, names=wins.index,
                        title=f"{team1} vs {team2} Head-to-Head")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No matches found between these teams with current filters")
    
    with tab3:
        st.subheader("Team Performance by Venue")
        team = st.selectbox("Select Team", sorted(filtered_df['team1'].unique()))
        venue_perf = filtered_df[(filtered_df['team1'] == team) | (filtered_df['team2'] == team)]
        venue_perf = venue_perf[venue_perf['winner'] == team]['venue'].value_counts().reset_index()
        venue_perf.columns = ['Venue', 'Wins']
        
        if not venue_perf.empty:
            fig = px.bar(venue_perf, x='Venue', y='Wins', color='Wins',
                        title=f"{team}'s Performance by Venue")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No wins found for {team} with current filters")

# Page 3: Match Analysis
elif page == "🎯 Match Analysis":
    st.header("Detailed Match Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Toss Impact Analysis")
        filtered_df['toss_impact'] = filtered_df['toss_winner'] == filtered_df['winner']
        toss_impact = filtered_df['toss_impact'].value_counts(normalize=True) * 100
        fig = px.pie(toss_impact, values=toss_impact.values, 
                    names=['Toss Winner Won', 'Toss Winner Lost'],
                    title="Toss Winner Match Outcome")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Toss Decision Analysis")
        toss_dec = filtered_df['toss_decision'].value_counts()
        fig = px.bar(toss_dec, x=toss_dec.index, y=toss_dec.values,
                    color=toss_dec.index, title="Toss Decisions")
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Margin of Victory Analysis")
    victory_type = st.radio("Select Victory Type", ['By Runs', 'By Wickets', 'Both'], horizontal=True)
    
    if victory_type != 'Both':
        df_vic = filtered_df[filtered_df['result'] == ('runs' if victory_type == 'By Runs' else 'wickets')]
    else:
        df_vic = filtered_df[filtered_df['result'].isin(['runs', 'wickets'])]
    
    if not df_vic.empty:
        fig = px.box(df_vic, x='result', y='result_margin', color='result',
                    title="Margin of Victory Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for selected filters")

# Page 4: Trends Over Time
elif page == "📈 Trends Over Time":
    st.header("Historical Trends Analysis")
    
    trend_option = st.selectbox("Select Trend to Analyze", 
                              ["Team Performance Over Seasons", 
                               "Toss Decision Trends", 
                               "Match Result Types Over Time"])
    
    if trend_option == "Team Performance Over Seasons":
        st.subheader("Team Performance Over Seasons")
        selected_teams_trend = st.multiselect("Select Teams to Compare", 
                                            sorted(df['team1'].unique()),
                                            default=['Mumbai Indians', 'Chennai Super Kings'])
        
        if selected_teams_trend:
            team_wins_over_time = filtered_df[filtered_df['winner'].isin(selected_teams_trend)]
            team_wins_over_time = team_wins_over_time.groupby(['season', 'winner']).size().reset_index()
            team_wins_over_time.columns = ['Season', 'Team', 'Wins']
            
            fig = px.line(team_wins_over_time, x='Season', y='Wins', color='Team',
                         title="Team Wins Over Seasons")
            st.plotly_chart(fig, use_container_width=True)
    
    elif trend_option == "Toss Decision Trends":
        st.subheader("Toss Decision Trends Over Time")
        toss_trend = filtered_df.groupby(['season', 'toss_decision']).size().reset_index()
        toss_trend.columns = ['Season', 'Decision', 'Count']
        
        fig = px.line(toss_trend, x='Season', y='Count', color='Decision',
                     title="Toss Decision Trends Over Seasons")
        st.plotly_chart(fig, use_container_width=True)
    
    elif trend_option == "Match Result Types Over Time":
        st.subheader("Match Result Types Over Time")
        result_trend = filtered_df.groupby(['season', 'result']).size().reset_index()
        result_trend.columns = ['Season', 'Result', 'Count']
        
        fig = px.area(result_trend, x='Season', y='Count', color='Result',
                     title="Match Result Types Over Seasons")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>Built with ❤️ by Diya using Streamlit | Data Source: IPL Official Records</p>
    <p>© 2023 IPL Dashboard Pro</p>
</div>
""", unsafe_allow_html=True)