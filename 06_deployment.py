# 06_deployment.py
import os
import subprocess
import sys
from datetime import datetime

def log_progress(message):
    """Log progress messages with timestamp"""
    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{time_stamp} : {message}")

def create_requirements_file():
    """Create requirements.txt for deployment"""
    requirements = """requests==2.31.0
pandas==2.0.3
numpy==1.24.3
textblob==0.17.1
beautifulsoup4==4.12.2
folium==0.14.0
matplotlib==3.7.2
seaborn==0.12.2
scikit-learn==1.3.0
flask==2.3.3
schedule==1.2.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    log_progress("✅ requirements.txt created")

def create_dockerfile():
    """Create Dockerfile for containerization"""
    dockerfile = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p templates static

# Expose port for Flask app
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/api/coverage-stats || exit 1

# Command to run the application
CMD ["python", "04_web_dashboard.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    log_progress("✅ Dockerfile created")

def create_docker_compose():
    """Create docker-compose.yml for easy deployment"""
    compose_file = """version: '3.8'

services:
  mobile-infrastructure-app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/coverage-stats"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add database service if using PostgreSQL instead of SQLite
  # postgres:
  #   image: postgres:13
  #   environment:
  #     POSTGRES_DB: mobile_infrastructure
  #     POSTGRES_USER: admin
  #     POSTGRES_PASSWORD: password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   ports:
  #     - "5432:5432"

volumes:
  postgres_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_file)
    
    log_progress("✅ docker-compose.yml created")

def create_deployment_script():
    """Create deployment script"""
    script = """#!/bin/bash

# Deployment Script for Mobile Infrastructure Analytics
echo "🚀 Deploying Mobile Infrastructure Analytics..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Deployment completed!"
echo "📊 Dashboard available at: http://localhost:5000"
echo "🔍 Check logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(script)
    
    # Make executable (Unix/Linux/Mac)
    if os.name != 'nt':  # Not Windows
        os.chmod('deploy.sh', 0o755)
    
    log_progress("✅ deploy.sh created")

def create_windows_deploy_script():
    """Create Windows deployment script"""
    script = """@echo off
echo 🚀 Deploying Mobile Infrastructure Analytics...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Build and start services
echo 📦 Building Docker images...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

echo ✅ Deployment completed!
echo 📊 Dashboard available at: http://localhost:5000
echo 🔍 Check logs: docker-compose logs -f
echo 🛑 Stop services: docker-compose down
"""
    
    with open('deploy.bat', 'w') as f:
        f.write(script)
    
    log_progress("✅ deploy.bat created")

def main():
    """Main deployment setup function"""
    log_progress("=== CREATING DEPLOYMENT CONFIGURATION ===")
    
    try:
        create_requirements_file()
        create_dockerfile()
        create_docker_compose()
        create_deployment_script()
        create_windows_deploy_script()
        
        log_progress("=== DEPLOYMENT CONFIGURATION COMPLETED ===")
        print("\n🎉 DEPLOYMENT FILES CREATED:")
        print("📋 requirements.txt - Python dependencies")
        print("🐳 Dockerfile - Container configuration")
        print("📦 docker-compose.yml - Multi-service setup")
        print("🚀 deploy.sh - Linux/Mac deployment script")
        print("🪟 deploy.bat - Windows deployment script")
        print("\nTo deploy:")
        print("1. Install Docker and Docker Compose")
        print("2. Run: ./deploy.sh (Linux/Mac) or deploy.bat (Windows)")
        print("3. Open: http://localhost:5000")
        
    except Exception as e:
        log_progress(f"❌ Error creating deployment files: {e}")

if __name__ == "__main__":
    main()