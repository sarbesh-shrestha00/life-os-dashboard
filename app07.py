
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai
import requests
from PIL import Image
from io import BytesIO


# ===============================
# CONFIG
# ===============================

st.set_page_config(
    page_title="Life-OS Dashboard",
    page_icon="🧠",
    layout="wide"
)


load_dotenv()


API_KEY = os.getenv("GEMINI_API_KEY")


client = genai.Client(
    api_key=API_KEY
)



# ===============================
# LOAD DATA
# ===============================


@st.cache_data
def load_data():

    df = pd.read_csv(
        "screentime.csv"
    )

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    return df



df = load_data()



# ===============================
# SIDEBAR
# ===============================


st.sidebar.title(
    "⚙️ Life Controls"
)


selected_day = st.sidebar.selectbox(
    "Choose Day",
    sorted(
        df["Date"].dt.date.unique(),
        reverse=True
    )
)


daily_goal = st.sidebar.slider(
    "Daily Screen Goal (Minutes)",
    60,
    600,
    240
)



# Filter selected day

today_df = df[
    df["Date"].dt.date == selected_day
]


# Bug #2 fix: idxmax() on an empty group raises ValueError.
# Stop the page cleanly instead of crashing.
if today_df.empty:

    st.error(
        "No data available for the selected day."
    )

    st.stop()



# ===============================
# HEADER
# ===============================


st.title(
    "🧠 Life-OS Wellbeing Dashboard"
)

st.caption(
    "AI powered productivity and lifestyle coach"
)



# ===============================
# KPI SECTION
# ===============================


total_minutes = today_df[
    "Minutes_Used"
].sum()


most_used = (
    today_df.groupby("App_Name")
    ["Minutes_Used"]
    .sum()
    .idxmax()
)


difference = total_minutes - daily_goal


# Single source of truth for how "bad" today was, reused by both
# the AI-output styling and the avatar generation below.
is_over_goal = total_minutes > daily_goal


col1,col2,col3 = st.columns(3)


with col1:

    st.metric(
        "Today's Screen Time",
        f"{total_minutes} min"
    )


with col2:

    st.metric(
        "Most Used App",
        most_used
    )


with col3:

    st.metric(
        "Goal Difference",
        f"{difference} min",
        delta=f"{difference} min",
        delta_color="inverse"
    )



# ===============================
# VISUALIZATION
# ===============================


trend = (
    df.groupby("Date")
    ["Minutes_Used"]
    .sum()
)


app_usage = (
    today_df.groupby("App_Name")
    ["Minutes_Used"]
    .sum()
)


left, right = st.columns(2)


with left:

    st.subheader(
        "📊 14 Day Screen Time Trend"
    )

    st.line_chart(
        trend
    )


with right:

    st.subheader(
        "Today's App Usage"
    )

    st.bar_chart(
        app_usage
    )



# Nice addition: category breakdown table so the AI analysis
# below is easy to verify at a glance.

st.subheader(
    "🗂️ Today's Category Breakdown"
)


st.dataframe(
    today_df.groupby("Category")["Minutes_Used"].sum()
)



# ===============================
# DATA BRIDGE
# ===============================


def create_ai_summary(data, selected_day, total_minutes, daily_goal, most_used):

    category_summary = (
        data.groupby("Category")
        ["Minutes_Used"]
        .sum()
    )

    return f"""
Date: {selected_day}
Total Screen Time: {total_minutes} minutes
Daily Goal: {daily_goal} minutes
Most Used App: {most_used}

Category Breakdown:
{category_summary.to_string()}
"""



summary = create_ai_summary(
    today_df,
    selected_day,
    total_minutes,
    daily_goal,
    most_used
)



# ===============================
# GEMINI AI COACH
# ===============================


def get_ai_coach(summary):


    prompt=f"""

You are Life-OS, a brutal but fair productivity coach.

Analyze this user's screen time:

{summary}


Rules:

1. Do not give generic advice.
2. Identify unhealthy patterns.
3. Explain what activities are stealing time.
4. Suggest real-world replacements.

Examples:

If entertainment is high:
suggest exercise, hobbies, reading.

If social media is high:
suggest conversations, outdoor activities.

If coding/education is high:
recognize productive behavior.

Give:
- Reality check
- Problems detected
- Action plan
- Tomorrow's challenge


Be honest but supportive.

"""


    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return f"⚠️ Couldn't reach Gemini right now: {e}"




# ===============================
# DISPLAY AI RESULT
# ===============================


st.subheader(
    "🤖 AI Life Coach"
)


if is_over_goal:

    st.warning(
        "⚠️ Your screen usage exceeded your goal"
    )

else:

    st.success(
        "🔥 Good control today"
    )


if st.button(
    "Analyze My Day"
):

    with st.spinner(
        "Gemini is analyzing..."
    ):

        advice = get_ai_coach(
            summary
        )

    # Requirement 10: render the Gemini analysis with st.markdown,
    # preceded by st.warning / st.info chosen by severity.
    if is_over_goal:

        st.warning(
            "Here's today's brutally honest breakdown 👇"
        )

    else:

        st.info(
            "Solid day — here's the full breakdown 👇"
        )

    st.markdown(
        advice
    )



# ===============================
# INNOVATION FEATURE
# GUILT TRIP AVATAR
# (Gemini evaluates the data and writes the image prompt itself,
#  as required, instead of a hardcoded if/else string.)
# ===============================


st.subheader(
    "🎭 Your Productivity Avatar"
)



def generate_avatar_prompt(summary, is_over_goal):

    tone = (
        "a lazy, guilt-inducing scene reflecting doomscrolling and wasted time"
        if is_over_goal else
        "an inspiring, high-energy scene reflecting focus and healthy habits"
    )

    prompt = f"""

You are an art director. Based on this user's screen time category breakdown:

{summary}

Write ONE short, vivid, single-sentence image generation prompt (max 25 words)
for a concept-art style illustration that captures {tone}.

Only output the image prompt itself. No preamble, no quotes, no explanation.

"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception:

        # Fallback keeps the feature usable even if Gemini is unreachable.
        if is_over_goal:
            return "a tired person glued to a glowing phone, surrounded by distractions, digital burnout concept art"
        else:
            return "a focused person using technology wisely, exercising and learning, productivity concept art"



if st.button(
    "Generate My Avatar"
):

    with st.spinner(
        "Gemini is designing your avatar..."
    ):

        prompt = generate_avatar_prompt(
            summary,
            is_over_goal
        )


    st.write(prompt)


    # Using Pollinations free image API

    url = (
        "https://image.pollinations.ai/prompt/"
        + prompt.replace(" ","%20")
    )


    try:

        response = requests.get(url, timeout=15)
        response.raise_for_status()

        img = Image.open(
            BytesIO(response.content)
        )

        st.image(
            img,
            caption="Your Life-OS Avatar"
        )

    except Exception as e:

        st.error(
            f"Couldn't generate the avatar image: {e}"
        )
