# 02_visualization.py
import pandas as pd
import sqlite3
import folium
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime

def log_progress(message):
    """Log progress messages with timestamp"""
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{time_stamp} : {message}")

def load_data_from_database():
    """Load data from SQLite database"""
    log_progress("Loading data from database...")
    
    conn = sqlite3.connect('european_mobile_infrastructure.db')
    
    # Load cell tower data
    df_cells = pd.read_sql('SELECT * FROM cell_towers', conn)
    
    # Load news data
    df_news = pd.read_sql('SELECT * FROM investment_news', conn)
    
    conn.close()
    
    log_progress(f"Loaded {len(df_cells)} cell towers and {len(df_news)} news articles")
    return df_cells, df_news

def create_cell_tower_map(df_cells):
    """Create interactive map of cell towers"""
    log_progress("Creating interactive cell tower map...")
    
    munich_center = [48.1351, 11.5820]
    m = folium.Map(location=munich_center, zoom_start=11)
    
    # Color by network type
    colors = {'2G': 'red', '3G': 'orange', '4G': 'blue', '5G': 'green'}
    
    for idx, row in df_cells.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=row['range'] / 1000,  # Scale circle size by range
            popup=f"""
            <b>Operator:</b> {row['operator']}<br>
            <b>Network:</b> {row['network_type']}<br>
            <b>Range:</b> {row['range']}m<br>
            <b>Signal:</b> {row['averageSignal']}dB<br>
            <b>Region:</b> {row['region_type']}
            """,
            color=colors.get(row['network_type'], 'gray'),
            fill=True,
            fillOpacity=0.6
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Network Types</b></p>
    <p><span style="color: red;">●</span> 2G (GSM)</p>
    <p><span style="color: orange;">●</span> 3G (UMTS)</p>
    <p><span style="color: blue;">●</span> 4G (LTE)</p>
    <p><span style="color: green;">●</span> 5G (NR)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save('munich_cell_tower_map.html')
    log_progress("✅ Interactive map saved as 'munich_cell_tower_map.html'")
    return m

def create_analytical_dashboards(df_cells, df_news):
    """Generate comprehensive visualizations"""
    log_progress("Creating analytical dashboards...")
    
    # Set style for better looking charts
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. NETWORK COVERAGE ANALYSIS
    fig1, axes1 = plt.subplots(2, 2, figsize=(15, 12))
    fig1.suptitle('Mobile Network Coverage Analysis - Munich Region', fontsize=16, fontweight='bold')
    
    # Network Type Distribution
    network_counts = df_cells['network_type'].value_counts()
    colors_network = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Blue, Orange, Green, Red
    axes1[0, 0].bar(network_counts.index, network_counts.values, color=colors_network)
    axes1[0, 0].set_title('Network Type Distribution', fontweight='bold')
    axes1[0, 0].set_ylabel('Number of Towers')
    axes1[0, 0].tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for i, v in enumerate(network_counts.values):
        axes1[0, 0].text(i, v + 10, str(v), ha='center', va='bottom', fontweight='bold')
    
    # Operator Market Share
    operator_counts = df_cells['operator'].value_counts()
    axes1[0, 1].pie(operator_counts.values, labels=operator_counts.index, autopct='%1.1f%%', startangle=90)
    axes1[0, 1].set_title('Operator Market Share', fontweight='bold')
    
    # Coverage Range by Network Type
    sns.boxplot(data=df_cells, x='network_type', y='range', ax=axes1[1, 0])
    axes1[1, 0].set_title('Coverage Range by Network Type', fontweight='bold')
    axes1[1, 0].set_xlabel('Network Type')
    axes1[1, 0].set_ylabel('Coverage Range (meters)')
    axes1[1, 0].tick_params(axis='x', rotation=45)
    
    # Tower Distribution by Region
    region_counts = df_cells['region_type'].value_counts()
    axes1[1, 1].bar(region_counts.index, region_counts.values, color='lightgreen')
    axes1[1, 1].set_title('Tower Distribution by Region', fontweight='bold')
    axes1[1, 1].set_ylabel('Number of Towers')
    axes1[1, 1].tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for i, v in enumerate(region_counts.values):
        axes1[1, 1].text(i, v + 10, str(v), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('network_coverage_analysis.png', dpi=300, bbox_inches='tight')
    log_progress("✅ Network coverage analysis saved as 'network_coverage_analysis.png'")
    
    # 2. SENTIMENT ANALYSIS DASHBOARD
    if len(df_news) > 0:
        fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
        fig2.suptitle('Investment News Sentiment Analysis', fontsize=16, fontweight='bold')
        
        # Sentiment Distribution
        sentiment_counts = df_news['sentiment_label'].value_counts()
        colors_sentiment = ['red', 'gray', 'green']
        axes2[0].bar(sentiment_counts.index, sentiment_counts.values, color=colors_sentiment)
        axes2[0].set_title('Sentiment Distribution', fontweight='bold')
        axes2[0].set_ylabel('Number of Articles')
        
        # Add value labels on bars
        for i, v in enumerate(sentiment_counts.values):
            axes2[0].text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
        # Sentiment Scores Scatter
        scatter = axes2[1].scatter(range(len(df_news)), df_news['sentiment_score'], 
                                  c=df_news['sentiment_score'], cmap='RdYlGn', s=100)
        axes2[1].set_title('Sentiment Scores', fontweight='bold')
        axes2[1].set_xlabel('Article Index')
        axes2[1].set_ylabel('Sentiment Score')
        axes2[1].axhline(y=0, color='red', linestyle='--', alpha=0.3)
        
        # Add colorbar
        plt.colorbar(scatter, ax=axes2[1])
        
        plt.tight_layout()
        plt.savefig('sentiment_analysis.png', dpi=300, bbox_inches='tight')
        log_progress("✅ Sentiment analysis saved as 'sentiment_analysis.png'")
    
    plt.show()
    log_progress("✅ All analytical dashboards created successfully!")

def main():
    """Main function for visualization phase"""
    log_progress("=== STARTING VISUALIZATION PHASE ===")
    
    try:
        # Load data from database
        df_cells, df_news = load_data_from_database()
        
        # Create visualizations
        create_cell_tower_map(df_cells)
        create_analytical_dashboards(df_cells, df_news)
        
        log_progress("=== VISUALIZATION PHASE COMPLETED ===")
        print("\n🎉 VISUALIZATION RESULTS:")
        print("📊 munich_cell_tower_map.html - Interactive map (open in browser)")
        print("📈 network_coverage_analysis.png - Network analysis charts")
        print("📊 sentiment_analysis.png - Sentiment analysis charts")
        
    except Exception as e:
        log_progress(f"❌ Error in visualization: {e}")

if __name__ == "__main__":
    main()