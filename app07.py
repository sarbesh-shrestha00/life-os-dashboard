import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from google import genai


# ===============================
# CONFIG
# ===============================

st.set_page_config(
    page_title="Life-OS Dashboard",
    page_icon="🧠",
    layout="wide"
)


# ===============================
# GEMINI API
# ===============================

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=API_KEY
    )

except Exception:
    st.error(
        "Gemini API key is missing. "
        "Add GEMINI_API_KEY in Streamlit Cloud Secrets."
    )
    st.stop()


# ===============================
# LOAD DATA
# ===============================

@st.cache_data
def load_data():

    df = pd.read_csv("screentime.csv")

    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    return df


df = load_data()


# ===============================
# SIDEBAR
# ===============================

st.sidebar.title("⚙️ Life Controls")


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


# ===============================
# FILTER SELECTED DAY
# ===============================

today_df = df[
    df["Date"].dt.date == selected_day
]


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
    today_df
    .groupby("App_Name")["Minutes_Used"]
    .sum()
    .idxmax()
)


difference = total_minutes - daily_goal


is_over_goal = (
    total_minutes > daily_goal
)


col1, col2, col3 = st.columns(3)


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
    df.groupby("Date")["Minutes_Used"]
    .sum()
)


app_usage = (
    today_df
    .groupby("App_Name")["Minutes_Used"]
    .sum()
)


left, right = st.columns(2)


with left:

    st.subheader(
        "📊 Screen Time Trend"
    )

    st.line_chart(
        trend
    )


with right:

    st.subheader(
        "📱 Today's App Usage"
    )

    st.bar_chart(
        app_usage
    )


# ===============================
# CATEGORY BREAKDOWN
# ===============================

st.subheader(
    "🗂️ Today's Category Breakdown"
)


category_breakdown = (
    today_df
    .groupby("Category")["Minutes_Used"]
    .sum()
    .sort_values(
        ascending=False
    )
)


st.dataframe(
    category_breakdown,
    use_container_width=True
)


# ===============================
# DATA BRIDGE
# ===============================

def create_ai_summary(
    data,
    selected_day,
    total_minutes,
    daily_goal,
    most_used
):

    category_summary = (
        data
        .groupby("Category")["Minutes_Used"]
        .sum()
    )

    app_summary = (
        data
        .groupby("App_Name")["Minutes_Used"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    return f"""
Date: {selected_day}

Total Screen Time:
{total_minutes} minutes

Daily Goal:
{daily_goal} minutes

Goal Difference:
{total_minutes - daily_goal} minutes

Most Used App:
{most_used}

Category Breakdown:
{category_summary.to_string()}

App Usage:
{app_summary.to_string()}
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

    prompt = f"""
You are Life-OS, a brutally honest but fair
productivity and lifestyle coach.

Analyze the user's screen-time data below.

{summary}

Rules:

1. Do not give generic advice.
2. Identify unhealthy patterns.
3. Explain which activities are consuming the most time.
4. Separate productive and unproductive usage.
5. Suggest realistic real-world replacements.
6. Be honest but supportive.
7. Keep the response easy to read.

Give your response using these sections:

## Reality Check

Give a short honest assessment.

## Problems Detected

List the biggest problems.

## What's Going Well

Mention productive behavior if present.

## Action Plan

Give 3-5 specific actions.

## Tomorrow's Challenge

Give one measurable challenge.

"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        return (
            "⚠️ Gemini could not analyze your data right now.\n\n"
            f"Error: {e}"
        )


# ===============================
# DISPLAY AI RESULT
# ===============================

st.subheader(
    "🤖 AI Life Coach"
)


if is_over_goal:

    st.warning(
        "⚠️ Your screen usage exceeded your goal."
    )

else:

    st.success(
        "🔥 Good control today!"
    )


if st.button(
    "🧠 Analyze My Day"
):

    with st.spinner(
        "Gemini is analyzing your day..."
    ):

        advice = get_ai_coach(
            summary
        )


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
# PRODUCTIVITY AVATAR
# ===============================

st.subheader(
    "🎭 Your Productivity Avatar"
)


def generate_avatar_prompt(
    summary,
    is_over_goal
):

    if is_over_goal:

        tone = """
a tired and distracted person surrounded by
phone notifications, endless scrolling,
digital distractions and wasted time
"""

    else:

        tone = """
a focused and energetic person balancing
technology, exercise, learning, hobbies
and healthy daily habits
"""


    prompt = f"""
You are a professional concept artist.

Analyze this user's screen-time data:

{summary}

Create ONE short, vivid image-generation prompt
for a concept-art illustration.

The image should communicate:

{tone}

Maximum 25 words.

Only output the image prompt.
Do not add explanations.
Do not use quotation marks.
"""


    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text.strip()


    except Exception:

        if is_over_goal:

            return (
                "a tired person glued to a glowing smartphone, "
                "surrounded by digital distractions, "
                "dark productivity burnout concept art"
            )

        else:

            return (
                "a focused person exercising, reading and "
                "using technology wisely, energetic "
                "productivity concept art"
            )


# ===============================
# GENERATE AVATAR
# ===============================

if st.button(
    "🎨 Generate My Avatar"
):

    with st.spinner(
        "Gemini is designing your avatar..."
    ):

        prompt = generate_avatar_prompt(
            summary,
            is_over_goal
        )


    st.write(
        "**AI Image Prompt:**"
    )

    st.write(
        prompt
    )


    # ===============================
    # POLLINATIONS IMAGE API
    # ===============================

    encoded_prompt = requests.utils.quote(
        prompt
    )


    url = (
        "https://image.pollinations.ai/prompt/"
        + encoded_prompt
    )


    try:

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()


        img = Image.open(
            BytesIO(
                response.content
            )
        )


        st.image(
            img,
            caption="Your Life-OS Productivity Avatar",
            use_container_width=True
        )


    except Exception as e:

        st.error(
            "Couldn't generate the avatar image."
        )

        st.write(
            f"Error: {e}"
        )


# ===============================
# FOOTER
# ===============================

st.divider()

st.caption(
    "🧠 Life-OS | AI-powered productivity and wellbeing dashboard"
)
