# India Finance Pulse

A small Flask-based dashboard that aggregates the latest Indian finance and markets headlines from multiple RSS feeds and shows them in a clean, dark UI.

## Features

- Aggregates news from:
  - Moneycontrol
  - Business Standard (Hindi, markets & share market)
  - The Hindu (markets)
  - Google News (India markets, Nifty, Sensex)
- Uses RSS (`feedparser`) and `requests` to fetch feeds.
- Normalises timestamps to India Standard Time (Asia/Kolkata).
- Pretty, card-based UI with source, time, and quick "Open story" links.
- Simple Flask server – easy to run locally or behind a production WSGI server.

## Tech Stack

- Python 3.9+ (recommended)
- [Flask](https://flask.palletsprojects.com/)
- [feedparser](https://feedparser.readthedocs.io/)
- [python-dateutil](https://dateutil.readthedocs.io/)
- [Requests](https://requests.readthedocs.io/)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/india-finance-pulse.git
cd india-finance-pulse
