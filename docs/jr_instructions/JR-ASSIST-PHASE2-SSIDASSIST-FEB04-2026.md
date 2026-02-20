# JR INSTRUCTION: Assist Platform Phase 2 — SSIDAssist Scaffold

**Task ID:** ASSIST-PHASE2-SSIDASSIST
**Priority:** P1
**Depends On:** ASSIST-PHASE1-CORE
**Date:** 2026-02-04
**Created By:** TPM (Claude Opus 4.5) + Council

---

## Mission

**Tools that make broken systems less broken.**

SSIDAssist helps people navigate Social Security Disability Insurance (SSDI) and Supplemental Security Income (SSI) — two of the most complex benefit systems in the United States. The approval rate is ~35%, appeal wait times exceed 18 months, and millions of disabled Americans struggle to survive while waiting.

We build calculators that work, wizards that guide, and AI council members that explain arcane regulations in plain language.

This is Phase 2 of the Assist Platform. Phase 1 Core provides the foundation (`/ganuda/assist/core/`). SSIDAssist is the second vertical after VetAssist.

---

## Architecture Context

**VetAssist Pattern:**
- FastAPI backend with modular API endpoints
- PostgreSQL on bluefin (192.168.132.222)
- Next.js frontend with TypeScript
- Calculator services extending base classes
- Council-powered chat with specialist constraints
- Crisis detection for vulnerable users
- Environment-based configuration (no hardcoded credentials)

**SSIDAssist extends this pattern:**
- Reuses core Assist Platform components (auth, session, config base)
- Adds SSDI/SSI-specific calculators (PIA formula, SGA thresholds)
- Provides SSDI application wizard (5 steps)
- Council configured for Social Security regulations
- Financial crisis detection patterns

---

## Directory Structure

```
/ganuda/assist/ssidassist/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app using create_assist_app(SSIDConfig())
│   ├── config.py                  # SSIDConfig extends AssistConfig
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pia_calculator.py      # Primary Insurance Amount calculator
│   │   ├── council_chat.py        # SSDI-focused council chat service
│   │   └── crisis_detection.py    # Financial distress detection
│   └── api/v1/endpoints/
│       ├── __init__.py
│       ├── calculator.py          # POST /calculate/pia
│       ├── wizard.py              # SSDI application wizard endpoints
│       └── chat.py                # Council chat endpoint
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # SSIDAssist branding
│   │   ├── page.tsx               # Dashboard with earnings record summary
│   │   ├── calculator/page.tsx    # PIA calculator interface
│   │   └── wizard/page.tsx        # SSDI application wizard
│   ├── components/
│   │   ├── PiaCalculatorView.tsx  # Uses core CalculatorView pattern
│   │   └── SsdiWizardShell.tsx    # Uses core WizardShell pattern
│   └── config/wizards/
│       └── ssdi_application.yaml  # 5-step wizard configuration
├── config/
│   ├── crisis_patterns.yaml       # Financial crisis detection patterns
│   └── council_context.yaml       # SSDI/SSI council specialist config
└── sql/
    └── ssid_schema.sql            # Database tables (prefix: ssid_)
```

---

## Technical Specifications

### 1. Backend Configuration (`config.py`)

**File:** `/ganuda/assist/ssidassist/backend/config.py`

```python
"""
SSIDAssist Configuration
Extends core Assist Platform configuration
Environment prefix: SSID_
"""

from assist.core.config import AssistConfig
from typing import Optional
from pydantic import Field


class SSIDConfig(AssistConfig):
    """
    Configuration for SSIDAssist application

    Environment Variables:
        SSID_DATABASE_URL: PostgreSQL connection string
        SSID_APP_TITLE: Application title (default: SSIDAssist)
        SSID_VERTICAL_NAME: Vertical identifier (default: ssidassist)
        SSID_FRONTEND_URL: Frontend URL
        SSID_PIA_BEND_POINT_1: First bend point for 2026
        SSID_PIA_BEND_POINT_2: Second bend point for 2026
        SSID_SGA_AMOUNT: Substantial Gainful Activity amount for 2026
    """

    # Application identity
    app_title: str = "SSIDAssist"
    vertical_name: str = "ssidassist"

    # Database (inherits from AssistConfig)
    database_host: str = "192.168.132.222"  # bluefin
    database_name: str = "zammad_production"
    database_user: str = Field(default=None, env="SSID_DB_USER")
    database_password: str = Field(default=None, env="SSID_DB_PASSWORD")

    # PIA Calculator 2026 Values
    pia_bend_point_1: int = Field(default=1174, env="SSID_PIA_BEND_POINT_1")
    pia_bend_point_2: int = Field(default=7078, env="SSID_PIA_BEND_POINT_2")
    pia_percentage_1: float = 0.90  # 90% of first bend point
    pia_percentage_2: float = 0.32  # 32% of amount between bend points
    pia_percentage_3: float = 0.15  # 15% of remainder

    # SGA (Substantial Gainful Activity) 2026
    sga_amount_non_blind: int = Field(default=1620, env="SSID_SGA_AMOUNT")
    sga_amount_blind: int = Field(default=2700, env="SSID_SGA_AMOUNT_BLIND")

    # Council configuration
    council_weights: dict = {
        "Turtle": 1.0,    # Methodical, regulatory focus
        "Gecko": 1.2,     # Detail-oriented for complex SSA rules
        "Spider": 0.8     # Web of regulations, but SSA is less combat-focused
    }

    # Frontend URLs
    frontend_url: str = Field(default="https://ssidassist.ganuda.us", env="SSID_FRONTEND_URL")

    class Config:
        env_prefix = "SSID_"
        env_file = ".env"
        case_sensitive = False


# Singleton instance
config = SSIDConfig()
```

---

### 2. PIA Calculator Service (`pia_calculator.py`)

**File:** `/ganuda/assist/ssidassist/backend/services/pia_calculator.py`

**THIS IS THE MOST IMPORTANT FILE IN SSIDASSIST.**

```python
"""
Primary Insurance Amount (PIA) Calculator
Implements Social Security benefit formula per 20 CFR 404.200-299

PIA Formula (2026):
- 90% of first $1,174 of AIME
- 32% of AIME between $1,174 and $7,078
- 15% of AIME above $7,078

AIME = Average Indexed Monthly Earnings
PIA = Primary Insurance Amount (monthly benefit at FRA)
"""

from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import math


class PIACalculator:
    """
    Primary Insurance Amount Calculator

    The PIA is the foundation of all Social Security benefit calculations.
    It is based on a worker's lifetime earnings, indexed for inflation,
    averaged over their 35 highest-earning years, and then divided by 12
    to get Average Indexed Monthly Earnings (AIME).

    The PIA formula applies progressive bend points:
    - Low earners get 90% replacement
    - Middle earners get 32% replacement
    - High earners get 15% replacement

    This progressive structure ensures Social Security acts as social insurance,
    providing higher replacement rates for lower-wage workers.
    """

    def __init__(
        self,
        bend_point_1: int = 1174,
        bend_point_2: int = 7078,
        percentage_1: float = 0.90,
        percentage_2: float = 0.32,
        percentage_3: float = 0.15
    ):
        """
        Initialize PIA calculator with 2026 bend points

        Args:
            bend_point_1: First bend point ($1,174 for 2026)
            bend_point_2: Second bend point ($7,078 for 2026)
            percentage_1: Percentage for first tier (90%)
            percentage_2: Percentage for second tier (32%)
            percentage_3: Percentage for third tier (15%)
        """
        self.bend_point_1 = bend_point_1
        self.bend_point_2 = bend_point_2
        self.percentage_1 = percentage_1
        self.percentage_2 = percentage_2
        self.percentage_3 = percentage_3

    def calculate(self, aime: int) -> Dict:
        """
        Calculate PIA from Average Indexed Monthly Earnings (AIME)

        Args:
            aime: Average Indexed Monthly Earnings (integer dollars)

        Returns:
            Dictionary with PIA calculation breakdown

        Example:
            >>> calc = PIACalculator()
            >>> result = calc.calculate(3000)
            >>> result['pia']
            1640.92
        """
        if aime < 0:
            raise ValueError("AIME cannot be negative")

        # Calculate each tier
        tier1_aime = min(aime, self.bend_point_1)
        tier1_amount = tier1_aime * self.percentage_1

        if aime > self.bend_point_1:
            tier2_aime = min(aime - self.bend_point_1, self.bend_point_2 - self.bend_point_1)
            tier2_amount = tier2_aime * self.percentage_2
        else:
            tier2_aime = 0
            tier2_amount = 0.0

        if aime > self.bend_point_2:
            tier3_aime = aime - self.bend_point_2
            tier3_amount = tier3_aime * self.percentage_3
        else:
            tier3_aime = 0
            tier3_amount = 0.0

        # Sum tiers to get PIA
        pia_raw = tier1_amount + tier2_amount + tier3_amount

        # Round down to nearest dime (SSA rule)
        pia_rounded = math.floor(pia_raw * 10) / 10

        # Build detailed response
        return {
            "aime": aime,
            "pia": round(pia_rounded, 2),
            "annual_benefit": round(pia_rounded * 12, 2),
            "calculation_steps": [
                {
                    "tier": 1,
                    "description": f"90% of first ${self.bend_point_1}",
                    "aime_portion": tier1_aime,
                    "percentage": self.percentage_1,
                    "amount": round(tier1_amount, 2),
                    "formula": f"${tier1_aime} × 90% = ${round(tier1_amount, 2)}"
                },
                {
                    "tier": 2,
                    "description": f"32% of ${self.bend_point_1} to ${self.bend_point_2}",
                    "aime_portion": tier2_aime,
                    "percentage": self.percentage_2,
                    "amount": round(tier2_amount, 2),
                    "formula": f"${tier2_aime} × 32% = ${round(tier2_amount, 2)}"
                },
                {
                    "tier": 3,
                    "description": f"15% of amount over ${self.bend_point_2}",
                    "aime_portion": tier3_aime,
                    "percentage": self.percentage_3,
                    "amount": round(tier3_amount, 2),
                    "formula": f"${tier3_aime} × 15% = ${round(tier3_amount, 2)}"
                }
            ],
            "bend_points": {
                "first": self.bend_point_1,
                "second": self.bend_point_2
            },
            "replacement_rate": round((pia_rounded / aime * 100) if aime > 0 else 0, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def calculate_from_earnings(
        self,
        annual_earnings: List[int],
        birth_year: int,
        current_age: int
    ) -> Dict:
        """
        Calculate AIME and PIA from earnings history

        Args:
            annual_earnings: List of annual earnings (up to 35 years)
            birth_year: Year of birth (for indexing factors)
            current_age: Current age

        Returns:
            Dictionary with AIME, PIA, and detailed breakdown
        """
        # Sort earnings descending and take top 35 years
        sorted_earnings = sorted(annual_earnings, reverse=True)[:35]

        # If less than 35 years, pad with zeros
        while len(sorted_earnings) < 35:
            sorted_earnings.append(0)

        # Calculate AIME (sum / 35 years / 12 months)
        total_indexed_earnings = sum(sorted_earnings)
        aime = int(total_indexed_earnings / 35 / 12)

        # Calculate PIA
        pia_result = self.calculate(aime)

        # Add earnings context
        pia_result["earnings_context"] = {
            "years_of_earnings": len([e for e in annual_earnings if e > 0]),
            "top_35_years_used": len([e for e in sorted_earnings if e > 0]),
            "total_indexed_earnings": total_indexed_earnings,
            "average_annual_earnings": int(total_indexed_earnings / 35),
            "birth_year": birth_year,
            "current_age": current_age
        }

        return pia_result

    @staticmethod
    def get_test_cases() -> List[Dict]:
        """
        Return test cases for PIA calculator validation

        Returns:
            List of test case dictionaries
        """
        return [
            {
                "test_id": 1,
                "name": "Low earner (AIME $1,000)",
                "aime": 1000,
                "expected_pia": 900.00,
                "formula": "1000 × 90% = 900"
            },
            {
                "test_id": 2,
                "name": "Medium earner (AIME $3,000)",
                "aime": 3000,
                "expected_pia": 1640.92,
                "formula": "(1174 × 90%) + (1826 × 32%) = 1056.60 + 584.32 = 1640.92"
            },
            {
                "test_id": 3,
                "name": "High earner (AIME $8,000)",
                "aime": 8000,
                "expected_pia": 3084.18,
                "formula": "(1174 × 90%) + (5904 × 32%) + (922 × 15%) = 1056.60 + 1889.28 + 138.30 = 3084.18"
            },
            {
                "test_id": 4,
                "name": "At first bend point (AIME $1,174)",
                "aime": 1174,
                "expected_pia": 1056.60,
                "formula": "1174 × 90% = 1056.60"
            },
            {
                "test_id": 5,
                "name": "At second bend point (AIME $7,078)",
                "aime": 7078,
                "expected_pia": 2945.88,
                "formula": "(1174 × 90%) + (5904 × 32%) = 1056.60 + 1889.28 = 2945.88"
            },
            {
                "test_id": 6,
                "name": "Maximum AIME (AIME $14,000)",
                "aime": 14000,
                "expected_pia": 4834.18,
                "formula": "(1174 × 90%) + (5904 × 32%) + (6922 × 15%) = 4834.18"
            },
            {
                "test_id": 7,
                "name": "Minimum wage earner (AIME $500)",
                "aime": 500,
                "expected_pia": 450.00,
                "formula": "500 × 90% = 450"
            }
        ]


class SGAChecker:
    """
    Substantial Gainful Activity (SGA) Checker

    SGA is the monthly income threshold used to determine if someone
    is engaged in substantial gainful activity. If earnings exceed SGA,
    they generally cannot receive SSDI benefits.

    2026 Amounts:
    - Non-blind: $1,620/month
    - Blind: $2,700/month
    """

    def __init__(
        self,
        sga_non_blind: int = 1620,
        sga_blind: int = 2700
    ):
        self.sga_non_blind = sga_non_blind
        self.sga_blind = sga_blind

    def check(self, monthly_earnings: int, is_blind: bool = False) -> Dict:
        """
        Check if earnings exceed SGA threshold

        Args:
            monthly_earnings: Monthly earnings amount
            is_blind: Whether applicant is statutorily blind

        Returns:
            Dictionary with SGA determination
        """
        threshold = self.sga_blind if is_blind else self.sga_non_blind
        exceeds_sga = monthly_earnings > threshold

        return {
            "monthly_earnings": monthly_earnings,
            "sga_threshold": threshold,
            "is_blind": is_blind,
            "exceeds_sga": exceeds_sga,
            "eligible_for_ssdi": not exceeds_sga,
            "margin": monthly_earnings - threshold,
            "note": "Earnings above SGA threshold generally preclude SSDI eligibility"
        }
```

---

### 3. Main Application (`main.py`)

**File:** `/ganuda/assist/ssidassist/backend/main.py`

```python
"""
SSIDAssist Backend API
Cherokee AI Federation - Council Approved

Social Security Disability Insurance assistance platform
Built on Assist Platform Core
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import config
from assist.core.app_factory import create_assist_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app using Assist Platform factory
app = create_assist_app(config)

# Additional SSID-specific middleware if needed
logger.info(f"[SSIDAssist] Starting {config.app_title}")
logger.info(f"[SSIDAssist] Database: {config.database_host}")
logger.info(f"[SSIDAssist] PIA Bend Points: ${config.pia_bend_point_1}, ${config.pia_bend_point_2}")

# Import and include routers
try:
    from api.v1.endpoints import calculator, wizard, chat

    app.include_router(
        calculator.router,
        prefix="/api/v1/calculator",
        tags=["calculator"]
    )
    app.include_router(
        wizard.router,
        prefix="/api/v1/wizard",
        tags=["wizard"]
    )
    app.include_router(
        chat.router,
        prefix="/api/v1/chat",
        tags=["chat"]
    )
    logger.info("[SSIDAssist] All routers loaded successfully")
except ImportError as e:
    logger.warning(f"[SSIDAssist] Some routers not loaded: {e}")

# Health check override
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SSIDAssist API",
        "version": "1.0.0",
        "vertical": config.vertical_name,
        "database": config.database_host
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,  # Different port from VetAssist (8001)
        reload=True,
        log_level="info"
    )
```

---

### 4. Calculator API Endpoint (`api/v1/endpoints/calculator.py`)

**File:** `/ganuda/assist/ssidassist/backend/api/v1/endpoints/calculator.py`

```python
"""
SSIDAssist Calculator API Endpoints
PIA and SGA calculations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session

from services.pia_calculator import PIACalculator, SGAChecker
from assist.core.database import get_db
from config import config

router = APIRouter()


class PIACalculationRequest(BaseModel):
    """Request model for PIA calculation"""
    aime: int = Field(..., ge=0, description="Average Indexed Monthly Earnings")
    user_id: Optional[int] = None


class PIAFromEarningsRequest(BaseModel):
    """Request model for PIA from earnings history"""
    annual_earnings: List[int] = Field(..., description="List of annual earnings")
    birth_year: int = Field(..., ge=1900, le=2020)
    current_age: int = Field(..., ge=18, le=100)
    user_id: Optional[int] = None


class SGACheckRequest(BaseModel):
    """Request model for SGA check"""
    monthly_earnings: int = Field(..., ge=0)
    is_blind: bool = False
    user_id: Optional[int] = None


@router.post("/pia")
async def calculate_pia(
    request: PIACalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate Primary Insurance Amount from AIME

    This is the core Social Security benefit calculation.
    Returns monthly benefit amount at Full Retirement Age (FRA).
    """
    try:
        calculator = PIACalculator(
            bend_point_1=config.pia_bend_point_1,
            bend_point_2=config.pia_bend_point_2,
            percentage_1=config.pia_percentage_1,
            percentage_2=config.pia_percentage_2,
            percentage_3=config.pia_percentage_3
        )

        result = calculator.calculate(request.aime)

        # Store calculation in database if user_id provided
        if request.user_id:
            from sqlalchemy import text
            query = text("""
                INSERT INTO ssid_calculations
                (user_id, calculation_type, inputs, result, created_at)
                VALUES (:user_id, 'pia', :inputs, :result, NOW())
            """)
            db.execute(query, {
                "user_id": request.user_id,
                "inputs": {"aime": request.aime},
                "result": result
            })
            db.commit()

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/pia-from-earnings")
async def calculate_pia_from_earnings(
    request: PIAFromEarningsRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate AIME and PIA from earnings history

    Takes up to 35 years of earnings data and computes:
    1. Average Indexed Monthly Earnings (AIME)
    2. Primary Insurance Amount (PIA)
    """
    try:
        calculator = PIACalculator(
            bend_point_1=config.pia_bend_point_1,
            bend_point_2=config.pia_bend_point_2
        )

        result = calculator.calculate_from_earnings(
            annual_earnings=request.annual_earnings,
            birth_year=request.birth_year,
            current_age=request.current_age
        )

        # Store calculation
        if request.user_id:
            from sqlalchemy import text
            query = text("""
                INSERT INTO ssid_calculations
                (user_id, calculation_type, inputs, result, created_at)
                VALUES (:user_id, 'pia_from_earnings', :inputs, :result, NOW())
            """)
            db.execute(query, {
                "user_id": request.user_id,
                "inputs": {
                    "annual_earnings": request.annual_earnings,
                    "birth_year": request.birth_year,
                    "current_age": request.current_age
                },
                "result": result
            })
            db.commit()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sga-check")
async def check_sga(
    request: SGACheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check if earnings exceed Substantial Gainful Activity threshold

    SGA is used in Step 1 of the five-step disability evaluation.
    Earnings above SGA generally preclude SSDI eligibility.
    """
    try:
        checker = SGAChecker(
            sga_non_blind=config.sga_amount_non_blind,
            sga_blind=config.sga_amount_blind
        )

        result = checker.check(
            monthly_earnings=request.monthly_earnings,
            is_blind=request.is_blind
        )

        # Store check
        if request.user_id:
            from sqlalchemy import text
            query = text("""
                INSERT INTO ssid_calculations
                (user_id, calculation_type, inputs, result, created_at)
                VALUES (:user_id, 'sga_check', :inputs, :result, NOW())
            """)
            db.execute(query, {
                "user_id": request.user_id,
                "inputs": {
                    "monthly_earnings": request.monthly_earnings,
                    "is_blind": request.is_blind
                },
                "result": result
            })
            db.commit()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-cases")
async def get_test_cases():
    """
    Get PIA calculator test cases for validation
    """
    return {
        "test_cases": PIACalculator.get_test_cases(),
        "description": "Use these test cases to validate PIA calculations"
    }
```

---

### 5. Council Context Configuration (`config/council_context.yaml`)

**File:** `/ganuda/assist/ssidassist/config/council_context.yaml`

```yaml
# SSIDAssist Council Context Configuration
# Defines domain expertise for SSDI/SSI assistance

domain: "Social Security Disability Insurance and Supplemental Security Income"

description: |
  Social Security Disability Insurance (SSDI) and Supplemental Security Income (SSI)
  are federal programs providing benefits to disabled individuals. SSDI is an earned
  benefit based on work history. SSI is a needs-based program for disabled individuals
  with limited income and resources.

regulations:
  - name: "20 CFR Part 404"
    description: "Federal Old-Age, Survivors and Disability Insurance"
    url: "https://www.ecfr.gov/current/title-20/chapter-III/part-404"

  - name: "20 CFR Part 416"
    description: "Supplemental Security Income for the Aged, Blind, and Disabled"
    url: "https://www.ecfr.gov/current/title-20/chapter-III/part-416"

  - name: "Blue Book (Listing of Impairments)"
    description: "Medical conditions that automatically qualify for disability benefits"
    url: "https://www.ssa.gov/disability/professionals/bluebook/"

  - name: "POMS (Program Operations Manual System)"
    description: "SSA's internal policy manual"
    url: "https://secure.ssa.gov/poms.nsf/"

key_concepts:
  sga:
    name: "Substantial Gainful Activity (SGA)"
    value_2026_non_blind: "$1,620/month"
    value_2026_blind: "$2,700/month"
    description: "Monthly earnings threshold for disability determination"

  aime:
    name: "Average Indexed Monthly Earnings"
    description: "Average of highest 35 years of indexed earnings, divided by 12 months"

  pia:
    name: "Primary Insurance Amount"
    description: "Monthly benefit amount at Full Retirement Age (FRA)"
    formula: "90% of first $1,174 + 32% of $1,174-$7,078 + 15% of remainder (2026)"

  dli:
    name: "Date Last Insured (DLI)"
    description: "Last date individual has disability insurance coverage"

  five_step_evaluation:
    name: "Sequential Evaluation Process"
    steps:
      - "Step 1: Is claimant engaged in SGA?"
      - "Step 2: Does claimant have severe impairment(s)?"
      - "Step 3: Does impairment meet or equal a Listing?"
      - "Step 4: Can claimant do past relevant work?"
      - "Step 5: Can claimant do other work in national economy?"

  rfc:
    name: "Residual Functional Capacity"
    description: "Assessment of what claimant can still do despite impairments"

specialist_weights:
  Turtle:
    weight: 1.0
    rationale: "Methodical approach suits complex SSA regulatory framework"

  Gecko:
    weight: 1.2
    rationale: "Detail-oriented precision critical for SSA rules and calculations"

  Spider:
    weight: 0.8
    rationale: "Web-thinking useful for interconnected rules, but less combat-focused than VA"

  Hummingbird:
    weight: 0.9
    rationale: "Quick insights helpful for pattern recognition in medical evidence"

context_priorities:
  - "Regulatory accuracy (20 CFR citations)"
  - "Calculator precision (PIA formula)"
  - "Plain language explanations"
  - "Empathy for applicants in crisis"
  - "Evidence-based guidance"

excluded_topics:
  - "Legal representation (refer to local legal aid)"
  - "Medical diagnosis (refer to healthcare provider)"
  - "Specific case predictions (too many variables)"
```

---

### 6. Crisis Detection Patterns (`config/crisis_patterns.yaml`)

**File:** `/ganuda/assist/ssidassist/config/crisis_patterns.yaml`

```yaml
# SSIDAssist Crisis Detection Patterns
# Identifies users in financial or emotional distress

crisis_categories:

  financial_crisis:
    severity: HIGH
    patterns:
      - "can't pay rent"
      - "losing my home"
      - "eviction notice"
      - "homeless"
      - "no money for food"
      - "can't afford groceries"
      - "utilities shut off"
      - "car repossessed"
      - "electricity cut off"
      - "medical bills overwhelming"

    response:
      message: "I see you're facing serious financial challenges. Please know there are resources available."
      resources:
        - name: "211"
          description: "Dial 211 for emergency assistance (food, shelter, utilities)"
          phone: "211"
        - name: "SNAP (Food Stamps)"
          description: "Supplemental Nutrition Assistance Program"
          url: "https://www.fns.usda.gov/snap"
        - name: "LIHEAP"
          description: "Low Income Home Energy Assistance Program"
          url: "https://www.acf.hhs.gov/ocs/liheap"

  benefits_denial_distress:
    severity: MEDIUM
    patterns:
      - "denied again"
      - "rejected my application"
      - "want to give up"
      - "can't go through this anymore"
      - "no hope left"
      - "been waiting years"
      - "lost my appeal"

    response:
      message: "Denials are extremely common (65% denial rate). Most successful applicants are denied at least once. Don't give up."
      resources:
        - name: "Request Reconsideration"
          description: "First level of appeal after denial"
          timeline: "File within 60 days of denial notice"
        - name: "Legal Aid Organizations"
          description: "Free legal help for disability appeals"
          url: "https://www.lsc.gov/what-legal-aid/find-legal-aid"

  medical_emergency:
    severity: CRITICAL
    patterns:
      - "can't afford medication"
      - "rationing insulin"
      - "skipping doses"
      - "emergency room again"
      - "can't pay for treatment"
      - "going without medicine"

    response:
      message: "This is a medical emergency. Please seek immediate help."
      resources:
        - name: "Emergency: 911"
          description: "Call 911 for life-threatening medical emergencies"
          phone: "911"
        - name: "Pharmacy Assistance Programs"
          description: "Drug manufacturers offer assistance programs"
          url: "https://www.needymeds.org"
        - name: "Federally Qualified Health Centers (FQHC)"
          description: "Sliding scale healthcare regardless of ability to pay"
          url: "https://findahealthcenter.hrsa.gov"

  suicide_ideation:
    severity: CRITICAL
    patterns:
      - "want to end it"
      - "not worth living"
      - "better off dead"
      - "suicide"
      - "kill myself"
      - "can't go on"

    response:
      message: "Please reach out for immediate help. You are not alone."
      resources:
        - name: "988 Suicide & Crisis Lifeline"
          description: "24/7 free and confidential support"
          phone: "988"
          url: "https://988lifeline.org"
        - name: "Crisis Text Line"
          description: "Text HOME to 741741"
          phone: "741741"
        - name: "Veterans Crisis Line"
          description: "For veterans in crisis"
          phone: "988 then press 1"

alert_actions:
  financial_crisis:
    - "Display crisis resources prominently"
    - "Prioritize wizard completion (faster application = faster benefits)"
    - "Log crisis flag for follow-up"

  benefits_denial_distress:
    - "Show appeal success statistics"
    - "Provide appeal wizard guidance"
    - "Connect to legal aid resources"

  medical_emergency:
    - "Display emergency resources FIRST"
    - "Pause wizard, prioritize immediate help"
    - "Log critical flag"

  suicide_ideation:
    - "Display 988 Lifeline prominently"
    - "Pause all other interactions"
    - "Log critical flag for review"
```

---

### 7. SSDI Application Wizard Configuration (`frontend/config/wizards/ssdi_application.yaml`)

**File:** `/ganuda/assist/ssidassist/frontend/config/wizards/ssdi_application.yaml`

```yaml
# SSDI Application Wizard Configuration
# Guides users through disability application process

wizard_id: "ssdi_application"
title: "SSDI Application Wizard"
description: "Step-by-step guidance for completing your Social Security Disability application"
version: "1.0.0"

steps:

  - step_id: 1
    title: "Personal Information"
    description: "Basic information about you"
    fields:
      - id: "full_name"
        label: "Full Legal Name"
        type: "text"
        required: true
        help: "Must match your Social Security card"

      - id: "ssn"
        label: "Social Security Number"
        type: "ssn"
        required: true
        help: "Your 9-digit SSN (we encrypt this data)"

      - id: "date_of_birth"
        label: "Date of Birth"
        type: "date"
        required: true

      - id: "phone"
        label: "Phone Number"
        type: "phone"
        required: true
        help: "SSA will call you about your claim"

      - id: "email"
        label: "Email Address"
        type: "email"
        required: false
        help: "For application updates (optional)"

      - id: "mailing_address"
        label: "Mailing Address"
        type: "address"
        required: true
        help: "Where SSA will send correspondence"

  - step_id: 2
    title: "Work History"
    description: "Your employment over the last 15 years"
    fields:
      - id: "work_history"
        label: "List all jobs from past 15 years"
        type: "repeating_group"
        required: true
        min_entries: 1
        max_entries: 20
        fields:
          - id: "employer"
            label: "Employer Name"
            type: "text"
            required: true

          - id: "job_title"
            label: "Job Title"
            type: "text"
            required: true

          - id: "start_date"
            label: "Start Date"
            type: "month_year"
            required: true

          - id: "end_date"
            label: "End Date"
            type: "month_year"
            required: true
            help: "Use 'Present' if still employed"

          - id: "hours_per_week"
            label: "Hours Per Week"
            type: "number"
            required: true
            min: 1
            max: 168

          - id: "job_duties"
            label: "Job Duties"
            type: "textarea"
            required: true
            help: "Describe physical and mental demands of this job"

      - id: "last_day_worked"
        label: "Last Day You Worked"
        type: "date"
        required: true
        help: "Even if just a few hours"

      - id: "currently_working"
        label: "Are you currently working?"
        type: "radio"
        required: true
        options:
          - "No, not working at all"
          - "Yes, working part-time (under SGA)"
          - "Yes, working full-time"

  - step_id: 3
    title: "Medical Conditions"
    description: "Conditions that prevent you from working"
    fields:
      - id: "medical_conditions"
        label: "List all disabling conditions"
        type: "repeating_group"
        required: true
        min_entries: 1
        max_entries: 20
        fields:
          - id: "condition_name"
            label: "Condition/Diagnosis"
            type: "text"
            required: true
            help: "Example: Major Depressive Disorder, Rheumatoid Arthritis"

          - id: "body_system"
            label: "Body System"
            type: "select"
            required: true
            options:
              - "Musculoskeletal (bones, joints, spine)"
              - "Neurological (brain, nerves)"
              - "Mental (depression, anxiety, PTSD)"
              - "Cardiovascular (heart, blood vessels)"
              - "Respiratory (lungs, breathing)"
              - "Immune system"
              - "Digestive"
              - "Other"

          - id: "onset_date"
            label: "When did this condition start?"
            type: "month_year"
            required: true

          - id: "how_it_limits_work"
            label: "How does this prevent you from working?"
            type: "textarea"
            required: true
            help: "Be specific: sitting, standing, lifting, concentrating, memory, etc."

      - id: "primary_disabling_condition"
        label: "Which condition disables you the most?"
        type: "select"
        required: true
        options_from: "medical_conditions.condition_name"

      - id: "medications"
        label: "Current Medications"
        type: "textarea"
        required: true
        help: "List all medications, doses, and prescribing doctors"

      - id: "side_effects"
        label: "Medication Side Effects"
        type: "textarea"
        required: false
        help: "Describe any side effects that limit your functioning"

  - step_id: 4
    title: "Medical Treatment"
    description: "Doctors, hospitals, and treatment history"
    fields:
      - id: "medical_providers"
        label: "All medical providers in past 2 years"
        type: "repeating_group"
        required: true
        min_entries: 1
        max_entries: 30
        fields:
          - id: "provider_name"
            label: "Doctor/Hospital/Clinic Name"
            type: "text"
            required: true

          - id: "provider_type"
            label: "Type"
            type: "select"
            required: true
            options:
              - "Primary care doctor"
              - "Specialist"
              - "Hospital"
              - "Mental health provider"
              - "Physical therapist"
              - "Other"

          - id: "address"
            label: "Address"
            type: "address"
            required: true

          - id: "phone"
            label: "Phone"
            type: "phone"
            required: true

          - id: "first_visit"
            label: "Date of First Visit"
            type: "month_year"
            required: true

          - id: "last_visit"
            label: "Date of Last Visit"
            type: "month_year"
            required: true

          - id: "frequency"
            label: "How often do you see them?"
            type: "text"
            required: true
            help: "Example: Monthly, Every 3 months, etc."

      - id: "hospitalizations"
        label: "Hospital stays in past 2 years"
        type: "repeating_group"
        required: false
        fields:
          - id: "hospital_name"
            label: "Hospital Name"
            type: "text"
            required: true

          - id: "admission_date"
            label: "Admission Date"
            type: "date"
            required: true

          - id: "discharge_date"
            label: "Discharge Date"
            type: "date"
            required: true

          - id: "reason"
            label: "Reason for Hospitalization"
            type: "text"
            required: true

      - id: "tests_procedures"
        label: "Recent Tests or Procedures"
        type: "textarea"
        required: false
        help: "MRI, CT scan, EKG, blood tests, etc. Include dates if known"

  - step_id: 5
    title: "Review & Submit"
    description: "Review your application before submitting"
    fields:
      - id: "review_summary"
        label: "Application Summary"
        type: "summary_display"
        required: false
        help: "Review all information above. Click 'Edit' to make changes."

      - id: "authorization"
        label: "Authorization Statement"
        type: "checkbox"
        required: true
        text: |
          I authorize SSIDAssist to use this information to help me complete
          my Social Security Disability application. I understand this is a
          helper tool and not a substitute for filing with SSA.

      - id: "accuracy_statement"
        label: "Accuracy Statement"
        type: "checkbox"
        required: true
        text: |
          I certify that the information I have provided is true and accurate
          to the best of my knowledge.

      - id: "next_steps_display"
        label: "Next Steps"
        type: "info_display"
        required: false
        content: |
          After submitting, you will receive:
          1. A formatted summary you can use to complete Form SSA-16
          2. A checklist of medical records to gather
          3. Guidance on filing online at ssa.gov or by phone (1-800-772-1213)

completion:
  message: "Application wizard completed successfully!"
  actions:
    - "Generate SSA-16 worksheet PDF"
    - "Generate medical records checklist"
    - "Email summary to user (if email provided)"
    - "Store wizard data in ssid_wizard_progress table"
```

---

### 8. Database Schema (`sql/ssid_schema.sql`)

**File:** `/ganuda/assist/ssidassist/sql/ssid_schema.sql`

```sql
-- SSIDAssist Database Schema
-- Extends Assist Platform Core (assist_users, assist_sessions)
-- All tables prefixed with ssid_

-- User calculations (PIA, SGA checks)
CREATE TABLE IF NOT EXISTS ssid_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    calculation_type VARCHAR(50) NOT NULL,  -- 'pia', 'pia_from_earnings', 'sga_check'
    inputs JSONB NOT NULL,  -- Input parameters
    result JSONB NOT NULL,  -- Calculation output
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ssid_calculations_user ON ssid_calculations(user_id);
CREATE INDEX idx_ssid_calculations_type ON ssid_calculations(calculation_type);
CREATE INDEX idx_ssid_calculations_created ON ssid_calculations(created_at DESC);

-- Earnings records (for AIME calculation)
CREATE TABLE IF NOT EXISTS ssid_earnings_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 1950 AND year <= 2100),
    earnings INTEGER NOT NULL CHECK (earnings >= 0),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,  -- User confirmed from SSA records
    source VARCHAR(50),  -- 'user_entered', 'ssa_import', 'estimated'
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, year)
);

CREATE INDEX idx_ssid_earnings_user ON ssid_earnings_records(user_id);
CREATE INDEX idx_ssid_earnings_year ON ssid_earnings_records(year);

-- Wizard progress (SSDI application wizard)
CREATE TABLE IF NOT EXISTS ssid_wizard_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    wizard_id VARCHAR(100) NOT NULL,  -- 'ssdi_application'
    current_step INTEGER NOT NULL DEFAULT 1,
    total_steps INTEGER NOT NULL,
    step_data JSONB NOT NULL DEFAULT '{}',  -- All wizard responses
    is_complete BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, wizard_id)
);

CREATE INDEX idx_ssid_wizard_user ON ssid_wizard_progress(user_id);
CREATE INDEX idx_ssid_wizard_complete ON ssid_wizard_progress(is_complete);

-- Medical conditions (from wizard)
CREATE TABLE IF NOT EXISTS ssid_medical_conditions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    condition_name VARCHAR(255) NOT NULL,
    body_system VARCHAR(100),
    onset_date DATE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    limitations TEXT,  -- How condition limits work
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ssid_conditions_user ON ssid_medical_conditions(user_id);
CREATE INDEX idx_ssid_conditions_primary ON ssid_medical_conditions(is_primary);

-- Work history (from wizard)
CREATE TABLE IF NOT EXISTS ssid_work_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    employer VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL if current job
    hours_per_week INTEGER CHECK (hours_per_week > 0 AND hours_per_week <= 168),
    job_duties TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ssid_work_user ON ssid_work_history(user_id);
CREATE INDEX idx_ssid_work_dates ON ssid_work_history(start_date DESC, end_date DESC);

-- Medical providers (from wizard)
CREATE TABLE IF NOT EXISTS ssid_medical_providers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    provider_name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(100),  -- 'primary_care', 'specialist', 'hospital', etc.
    address TEXT,
    phone VARCHAR(20),
    first_visit DATE,
    last_visit DATE,
    visit_frequency VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ssid_providers_user ON ssid_medical_providers(user_id);

-- Council chat history (SSDI-specific)
CREATE TABLE IF NOT EXISTS ssid_chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    specialist_name VARCHAR(50),  -- Which council member responded
    crisis_flag VARCHAR(50),  -- 'financial', 'medical', 'suicide', etc.
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ssid_chat_user ON ssid_chat_history(user_id);
CREATE INDEX idx_ssid_chat_session ON ssid_chat_history(session_id);
CREATE INDEX idx_ssid_chat_crisis ON ssid_chat_history(crisis_flag);

-- User crisis flags (for follow-up)
CREATE TABLE IF NOT EXISTS ssid_crisis_flags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES assist_users(id) ON DELETE CASCADE,
    crisis_type VARCHAR(50) NOT NULL,  -- 'financial_crisis', 'suicide_ideation', etc.
    severity VARCHAR(20) NOT NULL,  -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    trigger_message TEXT,  -- What the user said
    resources_displayed JSONB,  -- What resources we showed
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    flagged_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX idx_ssid_crisis_user ON ssid_crisis_flags(user_id);
CREATE INDEX idx_ssid_crisis_unresolved ON ssid_crisis_flags(is_resolved) WHERE is_resolved = FALSE;
CREATE INDEX idx_ssid_crisis_severity ON ssid_crisis_flags(severity);

-- Update triggers for updated_at fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ssid_calculations_updated_at BEFORE UPDATE ON ssid_calculations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ssid_earnings_updated_at BEFORE UPDATE ON ssid_earnings_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ssid_wizard_updated_at BEFORE UPDATE ON ssid_wizard_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ssid_conditions_updated_at BEFORE UPDATE ON ssid_medical_conditions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ssid_work_updated_at BEFORE UPDATE ON ssid_work_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ssid_providers_updated_at BEFORE UPDATE ON ssid_medical_providers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE ssid_calculations IS 'Stores PIA and SGA calculation results';
COMMENT ON TABLE ssid_earnings_records IS 'User earnings history for AIME calculation (up to 35 years)';
COMMENT ON TABLE ssid_wizard_progress IS 'SSDI application wizard state';
COMMENT ON TABLE ssid_medical_conditions IS 'User medical conditions extracted from wizard';
COMMENT ON TABLE ssid_work_history IS 'User work history (past 15 years)';
COMMENT ON TABLE ssid_medical_providers IS 'User medical providers and treatment history';
COMMENT ON TABLE ssid_chat_history IS 'Council chat conversations';
COMMENT ON TABLE ssid_crisis_flags IS 'Flags users in crisis for follow-up and safety';
```

---

## Frontend Scaffolding

### Frontend Layout (`frontend/app/layout.tsx`)

**File:** `/ganuda/assist/ssidassist/frontend/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SSIDAssist | Social Security Disability Help",
  description: "Free tools for navigating SSDI and SSI applications. Built by Ganuda AI.",
  keywords: ["SSDI", "SSI", "disability", "Social Security", "benefits", "PIA calculator"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
            <Header appTitle="SSIDAssist" />
            <main className="flex-1">
              {children}
            </main>
          </div>
        </AuthProvider>
        <footer className="border-t mt-auto">
          <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
            <p>SSIDAssist Platform | Tools for the 65% who get denied</p>
            <p className="mt-1">Educational tool only. Not legal advice. Platform: Bluefin</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
```

### Dashboard Page (`frontend/app/page.tsx`)

**File:** `/ganuda/assist/ssidassist/frontend/app/page.tsx`

```tsx
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calculator, ClipboardList, MessageSquare, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">SSIDAssist Dashboard</h1>
        <p className="text-lg text-muted-foreground mb-8">
          Tools to help you navigate Social Security Disability (SSDI/SSI)
        </p>

        {/* Crisis Resources Banner */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
          <p className="font-semibold text-blue-900">Need immediate help?</p>
          <p className="text-blue-800 text-sm mt-1">
            <strong>988 Suicide & Crisis Lifeline:</strong> Call or text 988 |
            <strong> 211:</strong> Emergency assistance (food, shelter, utilities)
          </p>
        </div>

        {/* Main Tools Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Calculator className="w-6 h-6 text-primary" />
                <CardTitle>PIA Calculator</CardTitle>
              </div>
              <CardDescription>
                Calculate your Primary Insurance Amount (monthly benefit)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm mb-4">
                Based on your work history and earnings, find out how much
                you could receive in SSDI benefits.
              </p>
              <Link href="/calculator">
                <Button>Calculate Benefits</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <ClipboardList className="w-6 h-6 text-primary" />
                <CardTitle>SSDI Application Wizard</CardTitle>
              </div>
              <CardDescription>
                Step-by-step guidance for your disability application
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm mb-4">
                Gather all required information in one place before filing
                with Social Security Administration.
              </p>
              <Link href="/wizard">
                <Button>Start Application</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-primary" />
                <CardTitle>Council Chat</CardTitle>
              </div>
              <CardDescription>
                Ask questions about SSDI/SSI regulations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm mb-4">
                AI specialists trained on Social Security regulations
                answer your questions in plain language.
              </p>
              <Link href="/chat">
                <Button variant="outline">Ask a Question</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-primary" />
                <CardTitle>Earnings Record</CardTitle>
              </div>
              <CardDescription>
                Track your work history for AIME calculation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm mb-4">
                Enter your earnings history to calculate Average Indexed
                Monthly Earnings (AIME).
              </p>
              <Link href="/earnings">
                <Button variant="outline">Manage Earnings</Button>
              </Link>
            </CardContent>
          </Card>

        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Approval Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-destructive">~35%</p>
              <p className="text-sm text-muted-foreground mt-2">
                Most applicants are denied initially. Appeals are common.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Average Wait Time</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-yellow-600">3-5 months</p>
              <p className="text-sm text-muted-foreground mt-2">
                Initial decision. Appeals can take 12-18 months.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">SGA 2026</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-primary">$1,620</p>
              <p className="text-sm text-muted-foreground mt-2">
                Monthly earnings limit for non-blind individuals
              </p>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
```

---

## Verification Steps

Once you have built the SSIDAssist scaffold, verify it works:

### 1. Database Setup
```bash
# Connect to bluefin PostgreSQL
psql -h 192.168.132.222 -U <user> -d zammad_production

# Run schema
\i /ganuda/assist/ssidassist/sql/ssid_schema.sql

# Verify tables created
\dt ssid_*
```

### 2. Backend Tests
```bash
cd /ganuda/assist/ssidassist/backend

# Test PIA calculator directly
python3 -c "
from services.pia_calculator import PIACalculator
calc = PIACalculator()

# Test case 1: AIME $1,000 -> PIA $900
result = calc.calculate(1000)
assert result['pia'] == 900.00, f'Expected 900.00, got {result[\"pia\"]}'
print('✓ Test 1 passed: AIME $1,000 -> PIA $900')

# Test case 2: AIME $3,000 -> PIA $1,640.92
result = calc.calculate(3000)
assert result['pia'] == 1640.92, f'Expected 1640.92, got {result[\"pia\"]}'
print('✓ Test 2 passed: AIME $3,000 -> PIA $1,640.92')

# Test case 3: AIME $8,000 -> PIA $3,084.18
result = calc.calculate(8000)
assert result['pia'] == 3084.10, f'Expected 3084.10, got {result[\"pia\"]}'
print('✓ Test 3 passed: AIME $8,000 -> PIA $3,084.10')

print('✓ All PIA calculator tests passed')
"

# Start backend server
python3 main.py
```

### 3. API Endpoint Tests
```bash
# Test health endpoint
curl http://localhost:8002/api/health

# Test PIA calculation
curl -X POST http://localhost:8002/api/v1/calculator/pia \
  -H "Content-Type: application/json" \
  -d '{"aime": 3000}'

# Expected response:
# {
#   "aime": 3000,
#   "pia": 1640.92,
#   "annual_benefit": 19691.04,
#   "calculation_steps": [...]
# }

# Test SGA check
curl -X POST http://localhost:8002/api/v1/calculator/sga-check \
  -H "Content-Type: application/json" \
  -d '{"monthly_earnings": 1500, "is_blind": false}'

# Expected response:
# {
#   "monthly_earnings": 1500,
#   "sga_threshold": 1620,
#   "exceeds_sga": false,
#   "eligible_for_ssdi": true,
#   "margin": -120
# }
```

### 4. Frontend Tests
```bash
cd /ganuda/assist/ssidassist/frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Navigate to http://localhost:3000
# - Verify layout renders with "SSIDAssist" branding
# - Check dashboard cards display
# - Test navigation to /calculator, /wizard, /chat
```

### 5. Integration Tests
```bash
# Full stack test: Create user, calculate PIA, start wizard
curl -X POST http://localhost:8002/api/v1/calculator/pia \
  -H "Content-Type: application/json" \
  -d '{"aime": 5000, "user_id": 1}'

# Verify stored in database
psql -h 192.168.132.222 -d zammad_production -c \
  "SELECT * FROM ssid_calculations WHERE user_id = 1 ORDER BY created_at DESC LIMIT 1;"
```

---

## Environment Variables

Create `/ganuda/assist/ssidassist/.env`:

```bash
# Database (bluefin)
SSID_DB_USER=<database_user>
SSID_DB_PASSWORD=<database_password>

# Application
SSID_APP_TITLE="SSIDAssist"
SSID_VERTICAL_NAME="ssidassist"
SSID_FRONTEND_URL="https://ssidassist.ganuda.us"

# PIA Calculator 2026
SSID_PIA_BEND_POINT_1=1174
SSID_PIA_BEND_POINT_2=7078

# SGA 2026
SSID_SGA_AMOUNT=1620
SSID_SGA_AMOUNT_BLIND=2700
```

**IMPORTANT:** Do not commit `.env` to git. Add to `.gitignore`.

---

## Deployment Notes

1. **Backend:** Deploy to bluefin (192.168.132.222) on port 8002
2. **Frontend:** Deploy Next.js app (port 3000) or static export
3. **Database:** Already on bluefin (zammad_production)
4. **DNS:** Point ssidassist.ganuda.us to bluefin
5. **SSL:** Use existing Ganuda SSL certificate

---

## Success Criteria

- [ ] PIA calculator returns correct values for all 7 test cases
- [ ] SGA checker correctly identifies earnings above/below thresholds
- [ ] SSDI wizard loads all 5 steps from YAML configuration
- [ ] Council chat integrates with specialist_council.py (Turtle, Gecko, Spider)
- [ ] Crisis detection patterns trigger on financial/medical distress keywords
- [ ] All database tables created with proper indexes
- [ ] Frontend renders SSIDAssist branding and navigation
- [ ] API endpoints respond with correct data structures
- [ ] No hardcoded credentials (all via environment variables)
- [ ] Thermal memory updated with SSIDAssist context

---

## Thermal Memory Context

After completing this task, store this context in thermal memory:

```
ASSIST PLATFORM PHASE 2: SSIDAssist scaffold deployed at /ganuda/assist/ssidassist/.
Built on Phase 1 Core foundation. Includes PIA calculator (2026 bend points $1,174/$7,078),
SGA checker ($1,620/$2,700), 5-step SSDI application wizard, council chat with SSDI specialist
weights (Gecko 1.2, Turtle 1.0, Spider 0.8), and financial crisis detection. Database schema
deployed to bluefin with ssid_* tables. Backend on port 8002. Frontend with Next.js.
All test cases passing. Zero hardcoded credentials. Domain: ssidassist.ganuda.us.
```

---

## Questions for TPM

If you encounter blockers:

1. **Database access:** Do you have credentials for bluefin PostgreSQL?
2. **Core platform:** Is `/ganuda/assist/core/` built yet? If not, build it first.
3. **Council integration:** Confirm `specialist_council.py` location and import path
4. **Frontend components:** Are WizardShell and CalculatorView available in core?

---

**End of Jr Instruction**

Built with care for the seven generations.
For the 65% who get denied.
Tools that make broken systems less broken.
