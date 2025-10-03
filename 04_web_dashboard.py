# 04_web_dashboard.py
from flask import Flask, render_template, jsonify, request
import pandas as pd
import sqlite3
import json
import folium
from datetime import datetime
import os

app = Flask(__name__)

def load_data():
    """Load data from database"""
    conn = sqlite3.connect('european_mobile_infrastructure.db')
    
    # Load all tables
    df_cells = pd.read_sql('SELECT * FROM cell_towers', conn)
    df_news = pd.read_sql('SELECT * FROM investment_news', conn)
    network_coverage = pd.read_sql('SELECT * FROM network_coverage', conn)
    regional_coverage = pd.read_sql('SELECT * FROM regional_coverage', conn)
    
    conn.close()
    return df_cells, df_news, network_coverage, regional_coverage

def create_dashboard_map():
    """Create interactive map for dashboard"""
    df_cells, _, _, _ = load_data()
    
    munich_center = [48.1351, 11.5820]
    m = folium.Map(location=munich_center, zoom_start=11)
    
    # Color by operator
    colors = {'Telekom': 'magenta', 'Vodafone': 'red', 'O2': 'blue'}
    
    for idx, row in df_cells.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            popup=f"""
            <b>{row['operator']}</b><br>
            <b>Network:</b> {row['network_type']}<br>
            <b>Signal:</b> {row['averageSignal']}dB<br>
            <b>Region:</b> {row['region_type']}
            """,
            color=colors.get(row['operator'], 'gray'),
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    # Save map
    m.save('templates/dashboard_map.html')
    return True

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/coverage-stats')
def coverage_stats():
    """API endpoint for coverage statistics"""
    df_cells, df_news, network_coverage, regional_coverage = load_data()
    
    stats = {
        'total_towers': len(df_cells),
        'total_articles': len(df_news),
        'operators': df_cells['operator'].value_counts().to_dict(),
        'network_types': df_cells['network_type'].value_counts().to_dict(),
        'regions': df_cells['region_type'].value_counts().to_dict(),
        'avg_signal': round(df_cells['averageSignal'].mean(), 2),
        'avg_range': round(df_cells['range'].mean(), 2),
        'sentiment_distribution': df_news['sentiment_label'].value_counts().to_dict() if 'sentiment_label' in df_news.columns else {}
    }
    
    return jsonify(stats)

@app.route('/api/tower-locations')
def tower_locations():
    """API endpoint for tower locations"""
    df_cells, _, _, _ = load_data()
    
    # Return limited data for performance
    towers_data = df_cells[['lat', 'lon', 'operator', 'network_type', 'averageSignal', 'region_type']].head(500).to_dict('records')
    return jsonify(towers_data)

@app.route('/api/network-coverage')
def network_coverage_data():
    """API endpoint for network coverage data"""
    _, _, network_coverage, _ = load_data()
    return jsonify(network_coverage.to_dict('records'))

@app.route('/api/regional-analysis')
def regional_analysis():
    """API endpoint for regional analysis"""
    _, _, _, regional_coverage = load_data()
    return jsonify(regional_coverage.to_dict('records'))

@app.route('/api/news-sentiment')
def news_sentiment():
    """API endpoint for news sentiment"""
    _, df_news, _, _ = load_data()
    
    sentiment_data = df_news[['title', 'source', 'date', 'sentiment_score', 'sentiment_label']].to_dict('records')
    return jsonify(sentiment_data)

@app.route('/api/operator-comparison')
def operator_comparison():
    """API endpoint for operator comparison"""
    df_cells, _, _, _ = load_data()
    
    operator_stats = df_cells.groupby('operator').agg({
        'lat': 'count',
        'averageSignal': 'mean',
        'range': 'mean'
    }).reset_index()
    
    operator_stats.columns = ['operator', 'tower_count', 'avg_signal', 'avg_range']
    operator_stats['avg_signal'] = operator_stats['avg_signal'].round(2)
    operator_stats['avg_range'] = operator_stats['avg_range'].round(2)
    
    return jsonify(operator_stats.to_dict('records'))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create the map for dashboard
    create_dashboard_map()
    
    print("🚀 Starting Mobile Infrastructure Dashboard...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🗺️ Interactive map available at: http://localhost:5000")
    print("⚡ API endpoints available at: http://localhost:5000/api/coverage-stats")
    
    app.run(debug=True, host='0.0.0.0', port=5000)