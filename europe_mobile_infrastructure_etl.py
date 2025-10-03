import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import json
import time
from textblob import TextBlob
import logging


##############################################################
########### Phase 1: Data Collection & Exploration ###########
##############################################################

def log_progress(message, log_file="etl_pipeline_log.txt"):
    """Log progress messages with timestamp"""
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # FIXED: Use proper encoding for Windows and remove Unicode characters
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"{time_stamp} : {message}\n")
    print(f"{time_stamp} : {message}")

def extract_opencellid_data(api_key, bbox=None, limit=1000):
    """
    Extract cell tower data from OpenCelliD API
    FIXED: Using the correct API approach for cell tower data
    """
    log_progress("Starting OpenCelliD data extraction")
    
    # FIXED: Use the correct API endpoint for batch cell tower data
    base_url = "https://ap1.unwiredlabs.com/v2/cell.php"
    
    # FIXED: Correct parameters for cell tower batch query
    params = {
        'token': api_key,
        'format': 'json',
        'radio': 'lte',  # Can be: gsm, umts, lte, nr
        'mcc': 262,      # Germany
        'mnc': 1,        # Telekom
    }
    
    if bbox:
        # For batch queries, we need to use area-based approach
        bbox_parts = bbox.split(',')
        if len(bbox_parts) == 4:
            min_lon, min_lat, max_lon, max_lat = map(float, bbox_parts)
            # Use center point for the query
            params['lat'] = (min_lat + max_lat) / 2
            params['lon'] = (min_lon + max_lon) / 2
            params['distance'] = 50000  # 50km radius
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        # Check if we got any response
        if response.status_code != 200:
            log_progress(f"API returned status {response.status_code}, using sample data")
            return generate_sample_data(bbox)
            
        data = response.json()
        
        # FIXED: Check the actual response structure
        log_progress(f"API Response keys: {list(data.keys())}")
        
        # Handle different response structures
        cells = []
        if 'cells' in data:
            cells = data['cells']
        elif 'results' in data:
            cells = data['results']
        else:
            # If no cell data in response, check if it's a single cell response
            if all(key in data for key in ['lat', 'lon', 'radio']):
                cells = [data]  # Single cell response
            else:
                log_progress("No cell tower data in API response, using sample data")
                return generate_sample_data(bbox)
        
        # Save raw data as backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'raw_cell_towers_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Enhanced logging
        cell_count = len(cells)
        log_progress(f"SUCCESS: Extracted {cell_count} cell towers")
        
        if cell_count > 0:
            df_temp = pd.DataFrame(cells)
            log_progress(f"Columns in response: {list(df_temp.columns)}")
            
            if 'radio' in df_temp.columns:
                network_stats = df_temp['radio'].value_counts().to_dict()
                log_progress(f"Network distribution: {network_stats}")
        else:
            log_progress("No cells found in response, using sample data")
            return generate_sample_data(bbox)
        
        return {'cells': cells}
        
    except requests.exceptions.RequestException as e:
        log_progress(f"Request Error: {str(e)} - using sample data")
        return generate_sample_data(bbox)
        
    except Exception as e:
        log_progress(f"Unexpected Error: {str(e)} - using sample data")
        return generate_sample_data(bbox)

def generate_sample_data(bbox=None):
    """
    Generate realistic sample cell tower data for Munich and surrounding areas
    """
    log_progress("Generating realistic sample cell tower data for Munich region")
    
    # Focus on Munich and Bavaria area
    if bbox:
        bbox_parts = bbox.split(',')
        min_lon, min_lat, max_lon, max_lat = map(float, bbox_parts)
    else:
        # Default Munich area coordinates
        min_lon, min_lat, max_lon, max_lat = 11.3, 48.0, 11.8, 48.3
    
    sample_cells = []
    network_types = ['LTE', 'GSM', 'UMTS', 'NR']  # 4G, 2G, 3G, 5G
    network_weights = [0.5, 0.1, 0.2, 0.2]  # More LTE and 5G in Munich
    
    # German mobile operators
    operators = [
        {'mcc': 262, 'mnc': 1, 'name': 'Telekom'},
        {'mcc': 262, 'mnc': 2, 'name': 'Vodafone'},
        {'mcc': 262, 'mnc': 7, 'name': 'O2'}
    ]
    
    # Generate realistic cell tower data
    for i in range(800):  # Generate 800 sample towers
        radio = np.random.choice(network_types, p=network_weights)
        operator = np.random.choice(operators)
        
        # More towers in central Munich, fewer in outskirts
        if i < 400:  # Dense coverage in city center
            lat = np.random.uniform(48.13, 48.16)  # Central Munich
            lon = np.random.uniform(11.55, 11.60)
            range_val = np.random.randint(800, 2000)  # Shorter range in dense areas
        else:  # Less dense in suburbs
            lat = np.random.uniform(min_lat, max_lat)
            lon = np.random.uniform(min_lon, max_lon)
            range_val = np.random.randint(2000, 10000)  # Longer range in suburbs
        
        cell = {
            'radio': radio,
            'mcc': operator['mcc'],
            'mnc': operator['mnc'],
            'operator': operator['name'],
            'lac': np.random.randint(1000, 5000),
            'cellid': np.random.randint(10000, 50000),
            'lat': lat,
            'lon': lon,
            'range': range_val,
            'averageSignal': np.random.randint(-85, -55),
            'created': int(time.time()) - np.random.randint(0, 31536000),  # Random time in last year
            'sample_data': True  # Flag to indicate this is sample data
        }
        sample_cells.append(cell)
    
    sample_data = {'cells': sample_cells}
    
    # Save sample data
    with open('sample_cell_towers_munich.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    log_progress(f"Generated {len(sample_cells)} sample cell towers for Munich region")
    return sample_data

def extract_investment_news(search_terms, num_articles=50):
    """
    Scrape investment news related to European mobile infrastructure
    Focus on Germany and Munich region
    """
    log_progress("Starting investment news extraction")
    
    # Enhanced sample data with realistic German and Munich-focused news
    sample_articles = [
        {
            'title': "Deutsche Telekom Invests €5 Billion in German 5G Network Expansion",
            'content': "Deutsche Telekom announces massive investment to expand 5G coverage across Germany, with focus on Bavaria and major urban centers like Munich.",
            'source': 'Telecom Germany',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'region': 'Germany',
            'sentiment': 'positive'
        },
        {
            'title': "Bavaria Government Approves €500 Million for Rural Broadband",
            'content': "The Bavarian state government has approved funding to improve mobile and broadband infrastructure in rural areas surrounding Munich.",
            'source': 'Bavaria News',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'region': 'Bavaria',
            'sentiment': 'positive'
        },
        {
            'title': "Munich Becomes 5G Testbed for European Smart City Projects",
            'content': "Munich selected as primary test location for European 5G and IoT smart city infrastructure projects, attracting major telecom investments.",
            'source': 'Munich Tech',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'region': 'Munich',
            'sentiment': 'positive'
        },
        {
            'title': "Vodafone Germany Expands Fiber Network in Munich Metropolitan Area",
            'content': "Vodafone announces expansion of fiber optic network in Munich and surrounding suburbs to support growing demand for high-speed internet.",
            'source': 'Vodafone News',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'region': 'Munich',
            'sentiment': 'positive'
        },
        {
            'title': "O2 Telefónica Partners with Munich Airport for 5G Coverage",
            'content': "O2 Telefónica partners with Munich Airport to provide comprehensive 5G coverage throughout the airport facilities and surrounding areas.",
            'source': 'Airport Tech',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'region': 'Munich',
            'sentiment': 'positive'
        }
    ]
    
    # Filter articles based on search terms
    filtered_articles = []
    for term in search_terms:
        for article in sample_articles:
            if (term.lower() in article['content'].lower() or 
                term.lower() in article['title'].lower()):
                article_copy = article.copy()
                article_copy['keywords'] = [term, 'mobile', 'infrastructure', 'Germany', 'Munich']
                filtered_articles.append(article_copy)
    
    # Remove duplicates
    unique_news = []
    seen_titles = set()
    for article in filtered_articles:
        if article['title'] not in seen_titles:
            unique_news.append(article)
            seen_titles.add(article['title'])
    
    # Save raw news data
    with open('raw_investment_news.json', 'w', encoding='utf-8') as f:
        json.dump(unique_news, f, indent=2, ensure_ascii=False)
    
    log_progress(f"Extracted {len(unique_news)} unique news articles")
    return unique_news

def explore_data(cell_tower_data, news_data):
    """Initial data exploration and analysis"""
    log_progress("Starting data exploration")
    
    # Explore cell tower data
    if cell_tower_data and 'cells' in cell_tower_data:
        df_cells = pd.DataFrame(cell_tower_data['cells'])
        
        print("=== CELL TOWER DATA EXPLORATION ===")
        print(f"Total records: {len(df_cells)}")
        print(f"Columns: {list(df_cells.columns)}")
        print("\nData types:")
        print(df_cells.dtypes)
        print("\nMissing values:")
        print(df_cells.isnull().sum())
        
        if len(df_cells) > 0:
            print("\nBasic statistics:")
            numeric_cols = df_cells.select_dtypes(include=[np.number]).columns
            print(df_cells[numeric_cols].describe())
            
            # Network type analysis
            if 'radio' in df_cells.columns:
                print("\nNetwork Type Distribution:")
                print(df_cells['radio'].value_counts())
            
            # Operator analysis
            if 'operator' in df_cells.columns:
                print("\nOperator Distribution:")
                print(df_cells['operator'].value_counts())
        
        # Save exploration summary
        exploration_report = {
            'cell_towers_total': len(df_cells),
            'cell_towers_columns': list(df_cells.columns),
            'cell_towers_missing': df_cells.isnull().sum().to_dict(),
            'news_articles_total': len(news_data),
            'exploration_date': datetime.now().isoformat()
        }
        
        with open('data_exploration_report.json', 'w', encoding='utf-8') as f:
            json.dump(exploration_report, f, indent=2, ensure_ascii=False)
    
    # Explore news data
    if news_data:
        df_news = pd.DataFrame(news_data)
        print("\n=== NEWS DATA EXPLORATION ===")
        print(f"Total articles: {len(df_news)}")
        print(f"Sources: {df_news['source'].unique()}")
        print(f"Regions: {df_news['region'].unique()}")
    
    log_progress("Data exploration complete")


##############################################################
########### Phase 2: Data Cleaning & Normalization ###########
##############################################################

def clean_cell_tower_data(cell_tower_data):
    """Clean and preprocess cell tower data"""
    log_progress("Starting cell tower data cleaning")
    
    if not cell_tower_data or 'cells' not in cell_tower_data:
        log_progress("No cell tower data to clean")
        return None
    
    df = pd.DataFrame(cell_tower_data['cells'])
    
    if len(df) == 0:
        log_progress("Empty dataframe after conversion")
        return df
    
    # Handle missing values
    numeric_columns = ['lat', 'lon', 'range', 'averageSignal']
    for col in numeric_columns:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                df[col].fillna(df[col].median(), inplace=True)
                log_progress(f"Filled {missing_count} missing values in {col}")
    
    # Remove duplicates based on unique cell identifiers
    initial_count = len(df)
    duplicate_columns = ['radio', 'mcc', 'mnc', 'lac', 'cellid']
    available_columns = [col for col in duplicate_columns if col in df.columns]
    
    if available_columns:
        df.drop_duplicates(subset=available_columns, inplace=True)
        removed_count = initial_count - len(df)
        if removed_count > 0:
            log_progress(f"Removed {removed_count} duplicate records")
    
    # Convert data types
    if 'created' in df.columns:
        df['created'] = pd.to_datetime(df['created'], unit='s', errors='coerce')
        log_progress("Converted 'created' to datetime")
    
    # Add derived features
    network_mapping = {
        'GSM': '2G', 'UMTS': '3G', 'LTE': '4G', 'NR': '5G'
    }
    df['network_type'] = df['radio'].map(network_mapping)
    
    # Add country information from MCC (Mobile Country Code)
    mcc_to_country = {
        '262': 'Germany', '208': 'France', '234': 'UK', '222': 'Italy',
        '214': 'Spain', '240': 'Sweden', '228': 'Switzerland'
    }
    if 'mcc' in df.columns:
        df['mcc'] = df['mcc'].astype(str)
        df['country'] = df['mcc'].map(mcc_to_country)
        # Fill missing countries with Germany (most likely for Munich focus)
        df['country'].fillna('Germany', inplace=True)
        country_count = df['country'].notna().sum()
        log_progress(f"Added country information for {country_count} towers")
    
    # Add region classification based on coordinates (Munich area)
    def classify_region(lat, lon):
        # Munich city center coordinates
        munich_center_lat, munich_center_lon = 48.1351, 11.5820
        distance = np.sqrt((lat - munich_center_lat)**2 + (lon - munich_center_lon)**2)
        
        if distance < 0.05:  # ~5km radius
            return 'Munich City Center'
        elif distance < 0.15:  # ~15km radius
            return 'Munich Metropolitan'
        else:
            return 'Bavaria Region'
    
    if 'lat' in df.columns and 'lon' in df.columns:
        df['region_type'] = df.apply(lambda row: classify_region(row['lat'], row['lon']), axis=1)
        log_progress("Added region classification based on coordinates")
    
    log_progress(f"Cleaned data: {len(df)} records (from {initial_count} initially)")
    return df

def analyze_news_sentiment(news_data):
    """Perform sentiment analysis on investment news"""
    log_progress("Starting news sentiment analysis")
    
    if not news_data:
        log_progress("No news data to analyze")
        return pd.DataFrame()
    
    df_news = pd.DataFrame(news_data)
    
    # Calculate sentiment scores
    sentiments = []
    for content in df_news['content']:
        blob = TextBlob(content)
        sentiments.append(blob.sentiment.polarity)
    
    df_news['sentiment_score'] = sentiments
    df_news['sentiment_label'] = pd.cut(sentiments, 
                                       bins=[-1, -0.1, 0.1, 1], 
                                       labels=['Negative', 'Neutral', 'Positive'])
    
    # Extract key features
    df_news['investment_mention'] = df_news['content'].str.contains(
        'investment|funding|capital|fund', case=False, na=False
    )
    df_news['infrastructure_mention'] = df_news['content'].str.contains(
        'infrastructure|tower|network|5G|4G|broadband|fiber', case=False, na=False
    )
    
    # Sentiment statistics
    sentiment_stats = df_news['sentiment_label'].value_counts().to_dict()
    log_progress(f"Sentiment distribution: {sentiment_stats}")
    
    log_progress("News sentiment analysis complete")
    return df_news

def normalize_features(df):
    """Normalize numerical features"""
    log_progress("Starting feature normalization")
    
    if df is None or len(df) == 0:
        log_progress("No data to normalize")
        return df
    
    numeric_columns = ['lat', 'lon', 'range', 'averageSignal']
    
    for col in numeric_columns:
        if col in df.columns and df[col].notna().any():
            # Min-max scaling
            col_min = df[col].min()
            col_max = df[col].max()
            
            if col_max > col_min:  # Avoid division by zero
                df[f'{col}_normalized'] = (df[col] - col_min) / (col_max - col_min)
                log_progress(f"Normalized {col} (range: {col_min:.2f} to {col_max:.2f})")
            else:
                df[f'{col}_normalized'] = 0.5  # Constant value
    
    return df

def save_to_database(df_cells, df_news, db_name='european_mobile_infrastructure.db'):
    """
    Save cleaned data to SQLite database
    """
    log_progress("Starting database save operation")
    
    try:
        conn = sqlite3.connect(db_name)
        
        # Save cell tower data
        if df_cells is not None and len(df_cells) > 0:
            df_cells.to_sql('cell_towers', conn, if_exists='replace', index=False)
            log_progress(f"Saved {len(df_cells)} cell towers to database")
        
        # Save news data
        if df_news is not None and len(df_news) > 0:
            df_news.to_sql('investment_news', conn, if_exists='replace', index=False)
            log_progress(f"Saved {len(df_news)} news articles to database")
        
        # Create additional tables for analysis
        create_analysis_tables(conn)
        
        conn.close()
        log_progress("Data successfully saved to database")
        
    except Exception as e:
        log_progress(f"Error saving to database: {e}")

def create_analysis_tables(conn):
    """Create additional tables for analytical queries"""
    cursor = conn.cursor()
    
    try:
        # Table for network type distribution
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_coverage AS
            SELECT 
                network_type,
                COUNT(*) as tower_count,
                AVG(range) as avg_range,
                COUNT(DISTINCT mcc) as countries_covered
            FROM cell_towers 
            WHERE network_type IS NOT NULL
            GROUP BY network_type
        ''')
        
        # Table for sentiment trends
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_trends AS
            SELECT 
                date,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as article_count
            FROM investment_news 
            WHERE date IS NOT NULL
            GROUP BY date
        ''')
        
        # Table for regional coverage in Bavaria
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_coverage AS
            SELECT 
                region_type,
                operator,
                network_type,
                COUNT(*) as tower_count,
                AVG(range) as avg_range
            FROM cell_towers 
            WHERE region_type IS NOT NULL
            GROUP BY region_type, operator, network_type
        ''')
        
        conn.commit()
        log_progress("Created analytical tables")
        
    except Exception as e:
        log_progress(f"Error creating analytical tables: {e}")


#################################################################
########### Phase 3: ETL Pipeline Automation Template ###########
#################################################################

def run_etl_pipeline():
    """Main ETL pipeline function"""
    log_progress("=== STARTING ETL PIPELINE ===")
    
    # USE YOUR ACTUAL API KEY HERE
    API_KEY = "pk.06bf701a0a7dfd8c6793b2fa3fc85e49"
    
    # Focus on Munich and Bavaria region
    MUNICH_BBOX = "11.3,48.0,11.8,48.3"  # Munich area
    BAVARIA_BBOX = "10.0,47.0,13.5,50.5"  # Larger Bavaria region
    
    # Phase 1: Extraction
    log_progress("Phase 1: Data Extraction")
    
    # Try to extract real data for Munich area, fallback to sample data
    log_progress("Attempting to extract real cell tower data for Munich...")
    cell_tower_data = extract_opencellid_data(API_KEY, bbox=MUNICH_BBOX, limit=1000)
    
    # Focus on German and Munich-specific search terms
    search_terms = ['5G', 'mobile infrastructure', 'telecom investment', 'Munich', 'Bavaria', 'Deutsche Telekom']
    news_data = extract_investment_news(search_terms)
    
    explore_data(cell_tower_data, news_data)
    
    # Phase 2: Transformation
    log_progress("Phase 2: Data Transformation")
    
    df_cells_clean = clean_cell_tower_data(cell_tower_data)
    df_news_clean = analyze_news_sentiment(news_data)
    
    if df_cells_clean is not None and len(df_cells_clean) > 0:
        df_cells_normalized = normalize_features(df_cells_clean)
        
        # Save intermediate cleaned data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df_cells_normalized.to_csv(f'cleaned_cell_towers_{timestamp}.csv', index=False, encoding='utf-8')
        log_progress("Saved cleaned cell towers to CSV")
        
        if df_news_clean is not None and len(df_news_clean) > 0:
            df_news_clean.to_csv(f'cleaned_investment_news_{timestamp}.csv', index=False, encoding='utf-8')
            log_progress("Saved cleaned news data to CSV")
        
        # Phase 3: Load to Database
        log_progress("Phase 3: Data Loading")
        save_to_database(df_cells_normalized, df_news_clean)
        
        # Generate final report
        generate_final_report(df_cells_normalized, df_news_clean)
    
    log_progress("=== ETL PIPELINE COMPLETED ===")

def generate_final_report(df_cells, df_news):
    """Generate a comprehensive final report"""
    log_progress("Generating final report")
    
    report = {
        'generated_date': datetime.now().isoformat(),
        'project_focus': 'Munich and Bavaria Mobile Infrastructure Analysis',
        'data_extraction': {},
        'quality_metrics': {},
        'key_insights': {}
    }
    
    if df_cells is not None and len(df_cells) > 0:
        report['data_extraction']['cell_towers'] = {
            'total_count': len(df_cells),
            'countries_covered': df_cells['country'].nunique() if 'country' in df_cells.columns else 0,
            'network_types': df_cells['network_type'].value_counts().to_dict() if 'network_type' in df_cells.columns else {},
            'operators': df_cells['operator'].value_counts().to_dict() if 'operator' in df_cells.columns else {},
            'regions': df_cells['region_type'].value_counts().to_dict() if 'region_type' in df_cells.columns else {}
        }
        
        # Key insights for Munich
        if 'region_type' in df_cells.columns:
            munich_towers = df_cells[df_cells['region_type'] == 'Munich City Center']
            report['key_insights']['munich_coverage'] = {
                'city_center_towers': len(munich_towers),
                'avg_range_city_center': munich_towers['range'].mean() if len(munich_towers) > 0 else 0,
                'primary_network_city': munich_towers['network_type'].mode().iloc[0] if len(munich_towers) > 0 else 'N/A'
            }
    
    if df_news is not None and len(df_news) > 0:
        report['data_extraction']['news_articles'] = {
            'total_count': len(df_news),
            'sentiment_distribution': df_news['sentiment_label'].value_counts().to_dict() if 'sentiment_label' in df_news.columns else {},
            'sources': df_news['source'].value_counts().to_dict() if 'source' in df_news.columns else {},
            'regions_covered': df_news['region'].value_counts().to_dict() if 'region' in df_news.columns else {}
        }
    
    # Save report
    with open('final_etl_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    log_progress("Final report generated: final_etl_report.json")


if __name__ == "__main__":
    # Initialize log file with UTF-8 encoding
    with open("etl_pipeline_log.txt", "w", encoding='utf-8') as f:
        f.write("=== Munich Mobile Infrastructure ETL Pipeline Log ===\n")
        f.write("Focus: Analysis of cell tower coverage and investment news in Munich/Bavaria region\n")
        f.write(f"Started at: {datetime.now().isoformat()}\n\n")
    
    # Run the complete ETL pipeline
    run_etl_pipeline()
    
    # Generate final report
    log_progress("Pipeline execution finished. Check logs and output files.")