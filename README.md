
# Life-OS Wellbeing Dashboard

An AI-powered screen time dashboard built with Streamlit and the Gemini API. It visualizes daily screen time, gives a brutal-but-fair AI coaching breakdown, and generates a mood avatar based on how the day went.

Built for the MirAI School of Technology "AI Builder" Track — Assignment 7.

## Features

- **Sidebar controls** — filter by day, set a daily screen time goal (minutes)
- **KPI row** — today's total screen time, most used app, and goal delta
- **Charts** — 14-day trend line chart and today's per-app usage bar chart
- **Category breakdown table** — quick view of usage by category
- **AI Life Coach** — sends today's usage summary to Gemini and displays a coaching report, styled based on whether you went over your goal
- **Productivity Avatar** — Gemini writes an image prompt based on your data, which is rendered using the Pollinations API

## Tech Stack

- streamlit
- pandas
- python-dotenv
- google-genai
- requests
- pillow

## Setup

1. Clone the repo:
   ```
   git clone https://github.com/<your-username>/life-os-wellbeing-dashboard.git
   cd life-os-wellbeing-dashboard
   ```

2. Create a virtual environment :
   ```
   python -m venv venv
   
   ```

3. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. Make sure `screentime.csv` is in the project root, with these columns:
   ```
   Date, App_Name, Category, Minutes_Used
   ```

## Run

```
streamlit run app.py
```

Then open the URL Streamlit prints in your terminal (usually `http://localhost:8501`).

## Project Structure

```
life-os-wellbeing-dashboard/
├── app.py
├── screentime.csv
├── requirements.txt
├── .env              (not committed)
├── .gitignore
└── README.md
```

## Notes

- If the Gemini API is unreachable (missing key, quota, no internet), the AI Coach and Avatar features show an on-screen error instead of crashing.
- If there's no data for the selected day, the dashboard shows an error and stops instead of throwing an exception.

- If gemini-2.5-flash is not working To fix this immediately, update the model string in your script from gemini-2.5-flash to gemini-2.0-flash (or gemini-1.5-flash).
