# 📈 Market Scan Engine

> **Intelligent stock pattern recognition tool that analyzes CSV portfolios and identifies bullish trading opportunities**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Overview

Market Scan Engine is a powerful web-based stock analysis platform that automatically scans your stock portfolio and identifies high-probability bullish chart patterns. Upload a CSV of ticker symbols and receive instant analysis across multiple technical indicators and patterns.

**Live Demo:** [https://mar-stocks.netlify.app](https://mar-stocks.netlify.app)

## ✨ Features

### 📊 **Pattern Recognition**
- **Cup & Handle Formation** - Classic continuation pattern indicating bullish breakout potential
- **Double Bottom** - Strong reversal pattern suggesting trend change
- **Support Bounce** - Stocks bouncing off key support levels
- **150-Day Moving Average** - Identifies stocks near critical psychological price points

### 🚀 **Technical Capabilities**
- Real-time stock data fetching via **yfinance API**
- Multi-threaded analysis for fast processing
- RESTful **API** architecture for scalability
- Responsive web interface with live results
- Session-based result caching for instant retrieval

### 🔒 **Reliable Infrastructure**
- **Backend Server:** FastAPI on Render
- **Frontend:** Netlify CDN deployment
- CORS-enabled cross-origin requests
- Error handling and validation

## 🏗️ Architecture

┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Frontend │────────▶│ FastAPI │────────▶│ yfinance │
│ (Netlify) │ HTTPS │ Backend │ API │ Market Data │
│ │◀────────│ (Render) │◀────────│ │
└─────────────────┘ └──────────────────┘ └─────────────────┘


## 📋 Prerequisites

- Python 3.8+
- pip package manager
- Git

## 🛠️ Installation (if you want to create Your Own ) Either With Out Sourced Servers Or Locally On Local Host ]


### 1️⃣ Clone the repository

### 2️⃣ Install dependencies

### 3️⃣ Run the development server / Run On LocalHost Just With Uvicorn
 
## 🚀 Deployment

### Backend (Render)
1. Connect your GitHub repository to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python Scraper.py`
4. Deploy

### Frontend (Netlify)
1. Connect your GitHub repository to Netlify
2. Set publish directory: `src/WebApp`
3. Add `_redirects` file for SPA routing
4. Deploy

## 🧪 Pattern Detection Algorithms

### Cup & Handle
- Identifies U-shaped price consolidation followed by small pullback
- Confirms with volume analysis and breakout criteria

### Double Bottom
- Detects two distinct lows at similar price levels
- Validates support strength and reversal momentum

### Support Bounce
- Calculates key support levels using historical pivots
- Identifies recent bounces with momentum indicators

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgments

- **yfinance** - Real-time market data API
- **FastAPI** - Modern Python web framework
- **Netlify** & **Render** - Deployment platforms

---

⭐ **Star this repository** if you found it helpful!

📊 **Built with Python** | 🚀 **Powered by FastAPI** | 💼 **For traders, by traders**
