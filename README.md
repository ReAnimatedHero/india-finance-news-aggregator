India Finance Pulse

A lightweight Flask application that aggregates India-focused finance and market news from multiple RSS feeds. It fetches headlines from major business sources, normalizes timestamps to IST, filters recent stories, and displays everything in a clean, dark, responsive dashboard.

🚀 Introduction

India Finance Pulse provides a unified view of market-related updates—Nifty, Sensex, Indian business, and finance stories—pulled from various reliable RSS feeds.
The interface presents cards grouped by source, each containing headlines, timestamps, and story links, offering a fast snapshot of financial updates across India.

🛠️ Getting Started
1. Clone the repository
git clone https://github.com/<your-username>/india-finance-pulse.git
cd india-finance-pulse

2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# OR
.venv\Scripts\activate         # Windows

3. Install dependencies
pip install -r requirements.txt

4. Run the application
python app.py


Visit the dashboard:
http://localhost:5000/

⚙️ How It Works

A dictionary maps news sources to their RSS feed URLs.

Each feed is fetched with requests and parsed using feedparser.

All timestamps are normalized to Indian Standard Time (Asia/Kolkata).

A filtering mechanism highlights stories from the past 24 hours while ensuring at least one article per feed always appears.

All items are merged, sorted by most recent, and passed into the Flask template.

The UI renders a responsive, dark-themed grid showing:

Source name

Published time

Headline

External link to the story

This creates a clear, real-time snapshot of finance and market movement across India.

🔧 Configuration

Inside app.py, you can configure:

➤ RSS Feed Sources

The FEEDS dictionary controls which sources are included:

FEEDS = {
    "Moneycontrol": "https://...",
    "Business Standard": "https://...",
}

➤ Time Window for Recent News
HOURS_WINDOW = 24

➤ Filtering Logic

The function filter_last_window() ensures:

Only recent items (last X hours) are prioritized.

A fallback story exists for every feed even if nothing new is available.

➤ HTML / UI

The TEMPLATE variable contains all HTML and CSS.

🎨 Customisation

You can easily customize the application:

✔ Add or remove news sources

Edit entries in the FEEDS dict.

✔ Change the UI theme

Modify CSS inside the template block.

✔ Adjust data ordering

Edit sorting logic inside the main request handler.

✔ Expand metadata shown in cards

Add fields like author, category, or summary.

✔ Add pagination or infinite scrolling

Extend the Flask route and template.

🏭 Production Notes

For production deployment, it is recommended to use a WSGI server such as Gunicorn or uWSGI:

gunicorn -w 4 -b 0.0.0.0:8000 app:app


Enhance reliability by placing Nginx in front for:

SSL

Caching

Reverse proxy

Static file handling

🐳 Running with Docker (Optional)
1. Dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]

2. Build & Run
docker build -t india-finance-pulse .
docker run -p 5000:5000 india-finance-pulse


Access the dashboard at:
http://localhost:5000/

🤝 Contributing

Contributions are welcome!

You can contribute by:

Adding more finance/business RSS feeds

Improving UI/UX

Enhancing filtering logic

Implementing tests

Adding CI/CD pipelines

Improving documentation

Feel free to open issues or submit pull requests.
