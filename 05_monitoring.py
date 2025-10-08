# 05_monitoring.py
import schedule
import time
import pandas as pd
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import logging

def log_progress(message):
    """Log progress messages with timestamp"""
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{time_stamp} : {message}")

def check_coverage_thresholds():
    """Check for coverage issues and send alerts"""
    log_progress("Checking coverage thresholds...")
    
    conn = sqlite3.connect('european_mobile_infrastructure.db')
    df_cells = pd.read_sql('SELECT * FROM cell_towers', conn)
    conn.close()
    
    alerts = []
    
    # Check for areas with poor signal
    poor_signal_areas = df_cells[df_cells['averageSignal'] < -80]
    if len(poor_signal_areas) > 10:
        alert_msg = f"ALERT: {len(poor_signal_areas)} areas with poor signal strength (< -80dB)"
        alerts.append(alert_msg)
        log_progress(alert_msg)
    
    # Check for technology gaps (no 5G coverage in regions)
    no_5g_areas = df_cells.groupby('region_type').filter(
        lambda x: '5G' not in x['network_type'].values
    )
    if len(no_5g_areas) > 0:
        regions_without_5g = no_5g_areas['region_type'].unique()
        alert_msg = f"ALERT: No 5G coverage in regions: {list(regions_without_5g)}"
        alerts.append(alert_msg)
        log_progress(alert_msg)
    
    # Check for operator coverage gaps
    operator_coverage = df_cells.groupby(['region_type', 'operator']).size().unstack(fill_value=0)
    for region in operator_coverage.index:
        for operator in operator_coverage.columns:
            if operator_coverage.loc[region, operator] == 0:
                alert_msg = f"ALERT: {operator} has no coverage in {region}"
                alerts.append(alert_msg)
                log_progress(alert_msg)
    
    return alerts

def send_email_alert(alerts):
    """Send email alert (configure with your email settings)"""
    if not alerts:
        return
    
    # Configure these with your email settings
    sender_email = "your_email@example.com"
    receiver_email = "admin@example.com"
    password = "your_email_password"
    
    subject = "Mobile Infrastructure Alert"
    body = "\n".join(alerts)
    
    try:
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Uncomment and configure if you want email alerts
        # with smtplib.SMTP("smtp.example.com", 587) as server:
        #     server.starttls()
        #     server.login(sender_email, password)
        #     server.send_message(message)
        
        log_progress("📧 Email alert prepared (configure email settings to send)")
        
    except Exception as e:
        log_progress(f"❌ Email alert failed: {e}")

def run_monitoring_cycle():
    """Run one monitoring cycle"""
    log_progress("=== STARTING MONITORING CYCLE ===")
    
    alerts = check_coverage_thresholds()
    
    if alerts:
        send_email_alert(alerts)
        log_progress(f"🚨 {len(alerts)} alerts generated")
    else:
        log_progress("✅ All systems normal - no alerts")
    
    log_progress("=== MONITORING CYCLE COMPLETED ===")

def scheduled_monitoring():
    """Run monitoring on schedule"""
    log_progress("Starting scheduled monitoring...")
    
    # Schedule monitoring runs
    schedule.every(1).hours.do(run_monitoring_cycle)
    schedule.every().day.at("09:00").do(run_monitoring_cycle)  # Morning check
    schedule.every().day.at("17:00").do(run_monitoring_cycle)  # Evening check
    
    # Run immediately
    run_monitoring_cycle()
    
    log_progress("Monitoring scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        log_progress("Monitoring stopped by user")

if __name__ == "__main__":
    print("🔍 Mobile Infrastructure Monitoring System")
    print("Options:")
    print("1. Run one monitoring cycle")
    print("2. Start scheduled monitoring")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        run_monitoring_cycle()
    elif choice == "2":
        scheduled_monitoring()
    else:
        print("Invalid choice. Running one monitoring cycle...")
        run_monitoring_cycle()