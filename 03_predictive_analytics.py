import pandas as pd
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import folium
from datetime import datetime

def log_progress(message):
    """Log progress messages with timestamp"""
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{time_stamp} : {message}")

def load_data():
    """Load data from database"""
    conn = sqlite3.connect('european_mobile_infrastructure.db')
    df_cells = pd.read_sql('SELECT * FROM cell_towers', conn)
    conn.close()
    return df_cells

def identify_coverage_gaps(df_cells):
    """Identify areas with poor coverage using clustering"""
    log_progress("Identifying coverage gaps...")
    
    # Prepare data for clustering
    coords = df_cells[['lat', 'lon']].values
    
    # Use DBSCAN to find dense areas (good coverage) and sparse areas (gaps)
    clustering = DBSCAN(eps=0.01, min_samples=5).fit(coords)
    df_cells['coverage_density'] = clustering.labels_
    
    # Areas with label -1 are coverage gaps
    coverage_gaps = df_cells[df_cells['coverage_density'] == -1]
    
    log_progress(f"✅ Identified {len(coverage_gaps)} potential coverage gap areas")
    return coverage_gaps, df_cells

def predict_optimal_tower_locations(df_cells, gap_areas):
    """Predict optimal locations for new towers"""
    log_progress("Predicting optimal tower locations...")
    
    # Prepare features for prediction
    X = df_cells[['lat', 'lon', 'range', 'averageSignal']].fillna(0)
    y = df_cells['range']
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Predict optimal range for gap areas
    if len(gap_areas) > 0:
        gap_features = gap_areas[['lat', 'lon', 'range', 'averageSignal']].fillna(0)
        optimal_ranges = model.predict(gap_features)
        
        log_progress(f"✅ Predicted optimal ranges for {len(gap_areas)} gap areas")
        return optimal_ranges
    else:
        log_progress("❌ No gap areas found for prediction")
        return np.array([])

def create_coverage_gap_map(df_cells, gap_areas, optimal_ranges):
    """Create map showing coverage gaps and optimal locations"""
    log_progress("Creating coverage gap map...")
    
    munich_center = [48.1351, 11.5820]
    m = folium.Map(location=munich_center, zoom_start=11)
    
    # Add existing towers
    for idx, row in df_cells.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=5,
            popup=f"{row['operator']} - {row['network_type']}",
            color='blue',
            fill=True,
            fillOpacity=0.6
        ).add_to(m)
    
    # Add coverage gaps
    for idx, row in gap_areas.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=8,
            popup=f"COVERAGE GAP - Signal: {row['averageSignal']}dB",
            color='red',
            fill=True,
            fillOpacity=0.8
        ).add_to(m)
    
    m.save('coverage_gap_analysis.html')
    log_progress("✅ Coverage gap map saved as 'coverage_gap_analysis.html'")
    return m

def main():
    """Main function for predictive analytics"""
    log_progress("=== STARTING PREDICTIVE ANALYTICS PHASE ===")
    
    try:
        # Load data
        df_cells = load_data()
        
        # Identify coverage gaps
        gap_areas, df_with_clusters = identify_coverage_gaps(df_cells)
        
        # Predict optimal locations
        optimal_ranges = predict_optimal_tower_locations(df_cells, gap_areas)
        
        # Create visualization
        create_coverage_gap_map(df_cells, gap_areas, optimal_ranges)
        
        log_progress("=== PREDICTIVE ANALYTICS COMPLETED ===")
        print(f"\n🎉 PREDICTION RESULTS:")
        print(f"🔍 Found {len(gap_areas)} coverage gap areas")
        print(f"🗺️ Map saved: coverage_gap_analysis.html")
        
    except Exception as e:
        log_progress(f"❌ Error in predictive analytics: {e}")

if __name__ == "__main__":
    main()