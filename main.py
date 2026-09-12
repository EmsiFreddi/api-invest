from enum import Enum
from decimal import Decimal, ROUND_HALF_UP

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="Investment Calculator API",
    description="Calculate the returns of an investment plan",
    version="1.0.0"
)


# ---------------------------------------
# ENUMS
# ---------------------------------------

class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class DurationUnit(str, Enum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


# ---------------------------------------
# DATA MODELS
# ---------------------------------------

class InvestmentPlan(BaseModel):
    initial_amount: float = Field(
        ...,
        ge=0,
        description="Initial investment amount"
    )

    profit_percentage: float = Field(
        ...,
        ge=0,
        description="Profit percentage per period"
    )

    profit_frequency: Frequency = Field(
        ...,
        description="How often the profit is applied"
    )

    periodic_contribution: float = Field(
        ...,
        ge=0,
        description="Amount added periodically"
    )

    contribution_frequency: Frequency = Field(
        ...,
        description="How often money is added"
    )

    duration: int = Field(
        ...,
        gt=0,
        description="Investment duration"
    )

    duration_unit: DurationUnit = Field(
        ...,
        description="Unit of the investment duration"
    )


class InvestmentResult(BaseModel):
    initial_amount: float
    total_contributions: float
    total_invested: float
    total_profit: float
    final_capital: float
    total_return_percentage: float
    number_of_periods: int
    evolution: list


# ---------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------

def convert_to_days(
    amount: int,
    unit: DurationUnit
) -> int:

    conversions = {
        DurationUnit.DAYS: 1,
        DurationUnit.WEEKS: 7,
        DurationUnit.MONTHS: 30,
        DurationUnit.YEARS: 365
    }

    return amount * conversions[unit]


def frequency_to_days(
    frequency: Frequency
) -> int:

    conversions = {
        Frequency.DAILY: 1,
        Frequency.WEEKLY: 7,
        Frequency.MONTHLY: 30,
        Frequency.YEARLY: 365
    }

    return conversions[frequency]


def round_money(value: float) -> float:
    """
    Round a monetary value to two decimal places.
    """

    return float(
        Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    )


# ---------------------------------------
# MAIN ENDPOINT
# ---------------------------------------

@app.post(
    "/calculate",
    response_model=InvestmentResult,
    summary="Calculate an investment plan"
)
def calculate_investment(plan: InvestmentPlan):

    if plan.profit_percentage > 100:
        raise HTTPException(
            status_code=400,
            detail="Profit percentage cannot exceed 100%"
        )

    # Convert the investment duration into days
    total_days = convert_to_days(
        plan.duration,
        plan.duration_unit
    )

    profit_period_days = frequency_to_days(
        plan.profit_frequency
    )

    contribution_period_days = frequency_to_days(
        plan.contribution_frequency
    )

    if total_days < profit_period_days:
        raise HTTPException(
            status_code=400,
            detail="Investment duration is shorter than the profit period"
        )

    # Initial capital
    capital = Decimal(str(plan.initial_amount))

    total_contributions = Decimal("0")

    profit_rate = (
        Decimal(str(plan.profit_percentage))
        / Decimal("100")
    )

    number_of_periods = total_days // profit_period_days

    evolution = []

    # Simulate the investment day by day
    for day in range(1, total_days + 1):

        # Add periodic contribution
        if day % contribution_period_days == 0:

            contribution = Decimal(
                str(plan.periodic_contribution)
            )

            capital += contribution
            total_contributions += contribution

        # Apply profit
        if day % profit_period_days == 0:

            profit = capital * profit_rate

            capital += profit

            evolution.append({
                "period": len(evolution) + 1,
                "day": day,
                "capital": round_money(float(capital)),
                "period_profit": round_money(float(profit)),
                "total_contributions": round_money(
                    float(total_contributions)
                )
            })

    # Calculate final results
    total_invested = (
        Decimal(str(plan.initial_amount))
        + total_contributions
    )

    total_profit = capital - total_invested

    total_return_percentage = Decimal("0")

    if total_invested > 0:
        total_return_percentage = (
            total_profit / total_invested
        ) * Decimal("100")

    return InvestmentResult(
        initial_amount=round_money(plan.initial_amount),
        total_contributions=round_money(
            float(total_contributions)
        ),
        total_invested=round_money(
            float(total_invested)
        ),
        total_profit=round_money(
            float(total_profit)
        ),
        final_capital=round_money(
            float(capital)
        ),
        total_return_percentage=round_money(
            float(total_return_percentage)
        ),
        number_of_periods=number_of_periods,
        evolution=evolution
    )


# ---------------------------------------
# HEALTH CHECK ENDPOINT
# ---------------------------------------

@app.get("/")
def root():

    return {
        "message": "Investment Calculator API is running",
        "documentation": "/docs"
    }