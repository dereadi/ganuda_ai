# KB-SARG-DATA-APIS: Sargassum Tracking Data Sources and APIs

**Date:** 2025-12-07
**Author:** TPM (Command Post)
**Category:** Research / Sargassum Project
**Priority:** HIGH
**Status:** INITIAL RESEARCH - NEEDS JR FOLLOW-UP

---

## Executive Summary

This KB documents available data sources for Sargassum bloom tracking and ocean current modeling. Key finding: USF has the best satellite tracking, NOAA has current data APIs. No single unified API exists - integration work needed.

---

## 1. USF Sargassum Watch System (SAWS)

**Organization:** USF College of Marine Science, Optical Oceanography Lab
**Lead Researchers:** Chuanmin Hu (Lab Director), Brian Barnes (Grant Lead)
**Funding:** $3.2M NOAA grant (2023-2028)

### What It Provides
- Near real-time satellite imagery of Sargassum abundance
- Interactive maps showing bloom locations
- Monthly bulletin with predictions
- Short-term trajectory forecasts (satellite + numerical models)

### Resolution
- **Current system:** Several kilometers
- **New system (2025):** ~50 meters (individual beach scale)

### Key URLs
- Main tracking: https://optics.marine.usf.edu/projects/saws.html
- Gulf/Straits/East Coast: https://new6.marine.usf.edu/Models/Sargassum/index.html
- Florida Bay region: https://ocgweb.marine.usf.edu/Models/Sargassum/flbay.html
- Lower Keys region: https://ocgweb.marine.usf.edu/Models/Sargassum/lokeys.html

### API Status
**UNKNOWN** - No public API documented. May need to contact lab directly.

### Partners
- Florida Atlantic University
- Caribbean Coastal Ocean Observing System (CariCOOS)
- NOAA Atlantic Oceanographic and Meteorological Laboratory
- U.S. Virgin Islands Department of Planning and Natural Resources

---

## 2. NOAA Ocean Current Data

### 2.1 CO-OPS Data Retrieval API (Real-time)

**Endpoint:** https://api.tidesandcurrents.noaa.gov/api/prod/
**Documentation:** https://tidesandcurrents.noaa.gov/web_services_info.html

**Features:**
- Real-time current measurements at PORTS stations
- 6-minute interval default
- Multiple formats: CSV, XML, KML, NetCDF, JSON, TXT, DODS
- Bin-based depth selection

**Limitation:** Station-based, not continuous coverage

### 2.2 OSCAR (Ocean Surface Current Analyses Real-time)

**Provider:** Earth and Space Research (ESR) via NASA/NOAA
**Viewer:** www.oscar.noaa.gov
**Data Access:** NASA Earthdata Harmony API
**Resolution:** 0.25 degree (~27km at equator)

**Dataset:** OSCAR_L4_OC_INTERIM_V2.0
**URL:** https://podaac.jpl.nasa.gov/dataset/OSCAR_L4_OC_INTERIM_V2.0

**Features:**
- Derived from satellite altimeter and scatterometer data
- Near-surface ocean current estimates
- Global coverage

### 2.3 Global RTOFS (Real-Time Ocean Forecast System)

**Model:** 1/12 degree eddy-resolving global HYCOM
**Operator:** NAVO (Naval Oceanographic Office)
**Forcing:** NCEP GFS winds
**Update:** Daily

**Data Access:**
- FTP: https://ftp.ocean.weather.gov/grids/operational/NCOM/regional/GRIB2/
- NOMADS: http://nomads.ncep.noaa.gov

### 2.4 Regional NCOM Models

**Resolution:** 1/36 degree (3km) - much better than OSCAR
**Coverage:** Regional (Caribbean coverage needs verification)

---

## 3. Global Ocean Currents Database (GOCD)

**URL:** https://www.ncei.noaa.gov/products/global-ocean-currents-database
**Type:** Historical archive (not real-time)
**Use Case:** Model training, pattern analysis

---

## 4. Integration Architecture (Proposed)

```
┌─────────────────────────────────────────────────────────────────┐
│                 CHEROKEE AI SARGASSUM TRACKER                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DATA INGESTION LAYER                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │ USF SAWS    │  │ OSCAR API   │  │ RTOFS/NCOM  │            │
│   │ (Imagery)   │  │ (Currents)  │  │ (Forecast)  │            │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│          │                │                │                    │
│          └────────────────┼────────────────┘                    │
│                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              CHEROKEE AI PREDICTION ENGINE              │   │
│   │  - Combine bloom location with current forecasts        │   │
│   │  - Calculate interception points                        │   │
│   │  - Generate arrival predictions by beach                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    WEBPAGE DISPLAY                       │   │
│   │  - Real-time bloom map                                   │   │
│   │  - Current vectors overlay                               │   │
│   │  - Predicted landfall locations                          │   │
│   │  - Interception point recommendations                    │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Research Tasks for Jr (FOLLOW-UP NEEDED)

### Immediate
1. Contact USF Optical Oceanography Lab about API/data access
2. Test OSCAR API - can we pull Caribbean current vectors?
3. Test CO-OPS API - what Caribbean stations exist?
4. Verify NCOM regional model Caribbean coverage

### Data Format Questions
- What format is USF satellite imagery? (GeoTIFF? NetCDF?)
- How frequently updated?
- Historical data availability for model training?

### Integration Questions
- Can we scrape the USF interactive maps if no API?
- CORS issues for client-side data fetching?
- Data licensing for commercial use?

---

## 6. Key Contacts

**USF Optical Oceanography Lab**
- Chuanmin Hu (Director)
- Brian Barnes (Sargassum Grant Lead)
- URL: https://optics.marine.usf.edu/

**CariCOOS (Caribbean coverage)**
- Partner on USF grant
- May have additional Caribbean-specific data

---

## References

- [USF Sargassum Watch System](https://optics.marine.usf.edu/projects/saws.html)
- [USF Sargassum News 2025](https://www.usf.edu/marine-science/news/2025/usf-experts-lead-on-sargassum-research-monitoring-and-prediction.aspx)
- [NOAA CO-OPS API](https://api.tidesandcurrents.noaa.gov/api/prod/)
- [OSCAR Dataset](https://podaac.jpl.nasa.gov/dataset/OSCAR_L4_OC_INTERIM_V2.0)
- [NOAA Tides & Currents Web Services](https://tidesandcurrents.noaa.gov/web_services_info.html)
- [Global Ocean Currents Database](https://www.ncei.noaa.gov/products/global-ocean-currents-database)

---

**Temperature:** 0.8 (Research Foundation)

**END OF KB-SARG-DATA-APIS**
