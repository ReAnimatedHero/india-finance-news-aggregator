# 🌐📈 India Finance Pulse

A lightweight Flask application that aggregates India-focused finance and market news from multiple RSS feeds. It fetches headlines from major business sources, normalizes timestamps to IST, filters recent stories, and displays everything in a clean, dark, responsive dashboard.

# 🚀 Introduction

India Finance Pulse provides a unified view of market-related updates—Nifty, Sensex, business, and finance headlines—from trusted RSS sources.
The dashboard presents cards grouped by source, each showing headlines, timestamps, and external links, giving you a fast digest of real-time market sentiment.

# 🛠️ Getting Started
🧭 1. Clone the repository
git clone https://github.com/<your-username>/india-finance-pulse.git
cd india-finance-pulse

🔒 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# OR
.venv\Scripts\activate         # Windows

📦 3. Install dependencies
pip install -r requirements.txt

▶️ 4. Run the app
python app.py


Visit: http://localhost:5000/

# ⚙️ How It Works

📡 RSS feeds are defined in a dictionary.

📰 Feeds are fetched using requests and parsed via feedparser.

🕒 Timestamps convert to IST for consistency.

🔍 Filtering logic highlights last-24-hour articles while ensuring each source shows at least one item.

📊 Items merge & sort (most recent first).

🎨 UI renders a grid of source cards with:

🔖 Headline

🕑 Published time

🔗 Article link

🏷️ Source name

🧩 Configuration

Everything is inside app.py:

📡 RSS Sources
FEEDS = {
    "Moneycontrol": "...",
    "Business Standard": "...",
}

⏱️ Time Window
HOURS_WINDOW = 24

# 🧠 Filtering Function

filter_last_window() ensures:

Recent items are prioritized

A fallback article exists for each feed

# 🎨 Template & UI

The TEMPLATE variable contains the HTML + CSS used for rendering.

# 🎛️ Customisation

Make the dashboard your own:

# ➕ Add or Remove Sources

Modify the FEEDS dict.

# 🎨 Change Theme / Colors

Edit CSS inside the template section.

# 🧹 Adjust Sorting

Change sorting logic in the main route.

# 📰 Show More Metadata

Add author, summary, category, etc.

# 🔄 Add Pagination or Infinite Scroll

Extend the UI inside the template.

# 🏭 Production Notes

Deploy using a WSGI server like Gunicorn:

gunicorn -w 4 -b 0.0.0.0:8000 app:app


For best performance, place Nginx in front for:

🔐 SSL

🚀 Caching

🔁 Reverse proxy

📂 Static handling

🐳 Running with Docker (Optional)
📄 Dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]

# ▶️ Build & Run
docker build -t india-finance-pulse .
docker run -p 5000:5000 india-finance-pulse


Visit: http://localhost:5000/

# 🤝 Contributing

Contributions are welcome!
You can help by:

📰 Adding more RSS sources

🎨 Improving UI/UX

🧠 Enhancing filtering logic

🧪 Adding tests

⚙️ Building CI workflows

📘 Improving docs

Feel free to open issues or submit PRs.
