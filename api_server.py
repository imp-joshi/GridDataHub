from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import urllib3
from requests.adapters import HTTPAdapter, Retry
from urllib3.util.ssl_ import create_urllib3_context
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a custom adapter to handle SSL
class CustomAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.options |= 0x4  # Enable legacy renegotiation
        context.check_hostname = False
        kwargs['ssl_context'] = context
        return super(CustomAdapter, self).init_poolmanager(*args, **kwargs)

# Create a session with the custom adapter and retry strategy
retry_strategy = Retry(
    total=3,  # Number of retries
    backoff_factor=1,  # Wait time between retries
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
    allowed_methods=["HEAD", "GET", "OPTIONS"]  # Retry only on these methods
)
adapter = CustomAdapter(max_retries=retry_strategy)
session = requests.Session()
session.verify = False
session.mount('https://', adapter)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the FastAPI app
app = FastAPI(
    title="Power Grid Data API",
    description="API for retrieving data from various regional power load dispatch centers",
    version="1.0.0"
)


# Define response models for consistency
class ERLDCData(BaseModel):
    StatId: int
    Date: str
    Time: str
    Freq: str
    RevNo: str
    DemandMet: str
    DSMMet: str


class SRLDCData(BaseModel):
    frequency: float
    allIndiaDemand: float
    sRDemand: float
    dsmRate: float
    timestamp: str


class NRLDCData(BaseModel):
    frequency: str
    all_india_demand: str
    nr_demand: str
    peak_demand_today: str
    nr_generation: str
    nr_re_generation: str
    current_sch_revision: str
    last_updated: str


class WRLDCData(BaseModel):
    date_time: str
    demand: str
    frequency: str
    deviation_rate: str
    renewable: str
    revision_nos: str


class AllRegionsData(BaseModel):
    erldc: Optional[ERLDCData] = None
    srldc: Optional[SRLDCData] = None
    nrldc: Optional[NRLDCData] = None
    wrldc: Optional[WRLDCData] = None
    timestamp: str


# Define API endpoints
@app.get("/erldc", response_model=ERLDCData)
async def get_erldc_data():
    try:
        erldc_api_url = "https://app.erldc.in/api/LiveDataScheduler/Get/RegionStatistics"
        response_erldc = session.get(erldc_api_url)
        response_erldc.raise_for_status()  # Raise an exception for HTTP errors
        data_erldc = response_erldc.json()
        
        # Log the raw data for debugging
        logger.info(f"ERLDC raw data: {data_erldc}")
        
        # Map the response to the ERLDCData model
        erldc_data = ERLDCData(
            StatId=data_erldc.get("StatId", 0),
            Date=data_erldc.get("Date", ""),
            Time=data_erldc.get("Time", ""),
            Freq=data_erldc.get("Freq", ""),
            RevNo=data_erldc.get("RevNo", ""),
            DemandMet=data_erldc.get("DemandMet", ""),
            DSMMet=data_erldc.get("DSMMet", "")
        )
        
        return erldc_data
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ERLDC data: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch ERLDC data: {str(e)}")


@app.get("/srldc", response_model=SRLDCData)
async def get_srldc_data():
    try:
        srldc_api_url = "https://www.srldc.in/indexPageDataInEvery5min"
        response_srldc = session.get(srldc_api_url)
        data_srldc = response_srldc.json()
        
        # Add processing timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_srldc["timestamp"] = current_time
        
        # Remove complex fields that might cause issues
        if 'localDate' in data_srldc:
            del data_srldc['localDate']
        if 'localDateForUpdate' in data_srldc:
            del data_srldc['localDateForUpdate']
            
        return data_srldc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SRLDC data: {str(e)}")


@app.get("/nrldc", response_model=NRLDCData)
async def get_nrldc_data():
    try:
        nrldc_url = "https://newnr.nrldc.in/"
        response_nrldc = session.get(nrldc_url)
        
        soup_nrldc = BeautifulSoup(response_nrldc.text, 'html.parser')
        content_divs = soup_nrldc.find_all('div', class_='content')
        
        result = {}
        for content_div in content_divs:
            h2 = content_div.find('h2', class_='m-0')
            p = content_div.find('p')
            if h2 and p:
                key = h2.text.strip().lower().replace(' ', '_')
                value = p.text.strip()
                result[key] = value
                
        return {
            "frequency": result.get("frequency", "N/A"),
            "all_india_demand": result.get("all_india_demand", "N/A"),
            "nr_demand": result.get("nr_demand", "N/A"),
            "peak_demand_today": result.get("peak_demand_today", "N/A"),
            "nr_generation": result.get("nr_generation", "N/A"),
            "nr_re_generation": result.get("nr_re_generation", "N/A"),
            "current_sch_revision": result.get("current_sch_revision", "N/A"),
            "last_updated": result.get("last_updated_on", "N/A"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch NRLDC data: {str(e)}")

@app.get("/wrldc", response_model=WRLDCData)
async def get_wrldc_data():
    try:
        wrldc_url = "https://wrldc.in/content/English/index.aspx"
        wrldc_response = session.get(wrldc_url)
        
        wrldc_soup = BeautifulSoup(wrldc_response.text, 'html.parser')
        box_elements = wrldc_soup.find_all('div', class_='box')
        
        data_dict = {}
        for box in box_elements:
            #span_text = box.find('span').text.strip()
            strong_element = box.find('strong')
            
            if strong_element:
                data_id = strong_element.get('id')
                data_value = strong_element.text.strip()
                if data_id == 'dataDateTime':
                    data_dict['date_time'] = data_value
                elif data_id == 'dataDemand':
                    data_dict['demand'] = data_value
                elif data_id == 'dataFrequency':
                    data_dict['frequency'] = data_value
                elif data_id == 'dataDeviationRate':
                    data_dict['deviation_rate'] = data_value
                elif data_id == 'dataRenewable':
                    data_dict['renewable'] = data_value
                elif data_id == 'dataRevision':
                    data_dict['revision_nos'] = data_value
        
        return data_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch WRLDC data: {str(e)}")

@app.get("/all", response_model=AllRegionsData)
async def get_all_data():
    try:
        # Initialize with the current timestamp
        result = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        # Try to get data from each API
        try:
            result["erldc"] = await get_erldc_data()
        except Exception:
            result["erldc"] = None
            
        try:
            result["srldc"] = await get_srldc_data()
        except Exception:
            result["srldc"] = None
            
        try:
            result["nrldc"] = await get_nrldc_data()
        except Exception:
            result["nrldc"] = None
            
        try:
            result["wrldc"] = await get_wrldc_data()
        except Exception:
            result["wrldc"] = None
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
