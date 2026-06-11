import streamlit as st
import pandas as pd
import pg8000
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="News Sentiment Dashboard", layout="wide")

st.title("📰 News Sentiment Dashboard")

refresh_seconds = st.sidebar.slider("Refresh every seconds", 5, 60, 10)

placeholder = st.empty()

def get_sentiment_label(score):
    if score >= 0.1:
        return "🟢 Positive"
    elif score <= -0.1:
        return "🔴 Negative"
    else:
        return "🟡 Neutral"

def load_data():
    conn = pg8000.connect(
        host="newsapii.ct6go4we2rqw.ap-south-1.rds.amazonaws.com",
        database="postgres",
        user="postgres",
        password="root1234567",
        port=5432
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            description,
            published_at,
            sentiment_score,
            created_at
        FROM news_articles
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "ID",
        "Title",
        "Description",
        "Published At",
        "Sentiment Score",
        "Created At"
    ])

    return df

try:
    df = load_data()

    with placeholder.container():

        st.success("Connected to RDS Successfully")

        if not df.empty:

            df["Sentiment"] = df["Sentiment Score"].apply(get_sentiment_label)
            df["Article"] = df["ID"].astype(str) + " - " + df["Title"]

            selected = st.selectbox(
                "Filter Sentiment",
                ["All", "🟢 Positive", "🔴 Negative", "🟡 Neutral"]
            )

            if selected != "All":
                filtered_df = df[df["Sentiment"] == selected]
            else:
                filtered_df = df

            st.subheader("News Articles")

            display_df = filtered_df[[
                "ID",
                "Title",
                "Description",
                "Published At",
                "Sentiment Score",
                "Sentiment",
                "Created At"
            ]]

            st.dataframe(
                display_df,
                use_container_width=True
            )

            st.subheader("Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Articles", len(df))

            with col2:
                avg_sentiment = round(df["Sentiment Score"].mean(), 2)
                st.metric("Average Sentiment", avg_sentiment)

            with col3:
                positive_count = len(df[df["Sentiment"] == "🟢 Positive"])
                st.metric("Positive Articles", positive_count)

            with col4:
                negative_count = len(df[df["Sentiment"] == "🔴 Negative"])
                st.metric("Negative Articles", negative_count)

            st.subheader("Sentiment Scores")

            if not filtered_df.empty:
                chart_df = filtered_df[["Article", "Sentiment Score"]]
                st.bar_chart(chart_df.set_index("Article"))
            else:
                st.warning("No data for selected sentiment.")

            st.subheader("Sentiment Distribution")

            sentiment_counts = df["Sentiment"].value_counts()

            col_left, col_right = st.columns([1, 1])

            with col_left:
                fig, ax = plt.subplots(figsize=(4, 4))
                ax.pie(
                    sentiment_counts,
                    labels=sentiment_counts.index,
                    autopct="%1.1f%%"
                )
                ax.set_title("Positive / Negative / Neutral News")
                st.pyplot(fig)

            with col_right:
                st.write("Sentiment Count")
                st.write(sentiment_counts)

        else:
            st.warning("No articles found in RDS.")

    time.sleep(refresh_seconds)
    st.rerun()

except Exception as e:
    st.error(f"Error: {str(e)}")