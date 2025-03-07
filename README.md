# GridDataHub

GridDataHub is an API server that aggregates power grid data from various regional load dispatch centers. It fetches data via both API calls and web scraping, transforming it into a consistent format for analysis and visualization.

## Features

- **Multiple Data Sources:**  
    - **SRLDC Data:** Fetches JSON data via API.
    - **ERLDC Data:** Retrieves data via an XML API.
    - **NRLDC Data:** Scrapes and parses HTML content for power grid metrics.
    - **WRLDC Data:** Extracts data from a web page using BeautifulSoup.
- **Aggregated Endpoint:**  
    - **/all:** Combines data from all sources into a single response.
- **Robust & Secure:**  
  - Custom SSL handling and a retry strategy for resilient data fetching.
- **Data Validation:**  
  - Pydantic models ensure consistent and reliable API responses.
- **Logging & Error Handling:**  
  - Comprehensive logging for debugging and error management.

## Getting Started

### Prerequisites

- Python 3.8 or later
- Install the required dependencies:

```bash
pip install fastapi uvicorn requests beautifulsoup4 pydantic urllib3
```

### Running the Server

Start the API server using uvicorn:

```bash
uvicorn api_server:app --reload
```

The server will run on [http://127.0.0.1:8000](http://127.0.0.1:8000).

### API Endpoints

- **GET `/erldc`:**  
  Returns ERLDC power grid data in a structured JSON format.
- **GET `/srldc`:**  
  Returns SRLDC data along with a processing timestamp.
- **GET `/nrldc`:**  
  Provides data scraped from the NRLDC website.
- **GET `/wrldc`:**  
  Delivers data scraped from the WRLDC website.
- **GET `/all`:**  
  Aggregates and returns data from all regions in a single response.

## Notebooks

The `notebooks/` directory contains Jupyter notebooks that provide examples of:
- Fetching and processing API data.
- Performing web scraping for grid data.
- Integrating data with external tools like Google Sheets.

