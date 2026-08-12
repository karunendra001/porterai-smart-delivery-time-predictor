# ?? Porter AI - Smart Delivery Time Predictor

An end-to-end Machine Learning web application that predicts delivery arrival times in real time, featuring interactive route animation, multi-vehicle comparisons (E-Bike, Express, Van), and live performance charts.

## ?? Key Features
- **Real-Time ML Inference:** Predicts delivery times based on market ID, store category, route distance, and active driver partners.
- **Dynamic Vehicle Mode Comparison:** Switch between E-Bikes, Express Fleets, and Standard Vans with live route animations and dynamic Chart.js visualizations.
- **Sub-12ms Latency:** Fast prediction throughput built on Flask and scikit-learn.
- **Single-Command Launch:** Node.js launcher integration (\server.js\) to run the Python server seamlessly with \
pm start\.

## ?? Quick Start Guide
\\\powershell
# 1. Activate virtual environment & install packages
.\.venv\Scripts\activate
pip install -r requirements.txt

# 2. Run the application
npm start
\\\`n
Access the dashboard at http://127.0.0.1:5000.
