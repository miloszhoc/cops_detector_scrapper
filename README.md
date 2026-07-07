# Cops Detector

Cops Detector is an automated system designed to identify and track unmarked police vehicles (undercover cars) in Poland. By leveraging web scraping, image recognition, and Large Language Models (LLMs), the project collects and processes data from social media groups to provide an up-to-date database of potential police vehicles.

## Features

- **Automated Scraping**: Utilizes [Playwright](https://playwright.dev/) to navigate and extract data from Facebook groups.
- **Multi-Source Support**: Handles both one-time historical data ingestion and periodic updates.
- **Cloud Integration**: Built with AWS in mind, using S3 for storage.
- **Data Joining & Normalization**: Tools to merge album data and normalize voivodeship information.

## Architecture

The system is composed of several key components:
- **Initial Scraper**: For one-time bulk data collection.
- **Periodic Scraper**: To keep the database updated with the latest reports.
- **Processing Pipeline**: AWS Lambda functions that trigger upon new data ingestion.
- **Storage**: AWS S3 for raw/processed images and metadata.

## Getting Started

### Prerequisites

- Python 3.10+
- [Playwright](https://playwright.dev/python/docs/intro)
- AWS Account

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/cops-detector.git
   cd cops-detector
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

### Configuration

Create a configuration file or set environment variables in `env_config/config.py` for:
- `BUCKET_NAME`: Your AWS S3 bucket.
- `PROJECT_ROOT_FOLDER`: Path to the project.

## Usage

### Run Periodic Scraper
To start the periodic scraping of configured Facebook groups:
```bash
python -m scrappers.periodic_scrapper
```

### Run One-Time Scraper
For initial data ingestion:
```bash
python -m scrappers.one_time_scrapper
```

## Project Structure

- `scrappers/`: Playwright-based scrapers and Page Object Model (POM) definitions.
- `utils/`: Helper scripts for logging, S3 operations, and data transformation.
- `env_config/`: Configuration settings and environment management.
- `.github/workflows/`: GitHub Actions for automated scraping tasks.

## Disclaimer

This project is for educational and informational purposes only.
