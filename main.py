import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

logger = logging.getLogger("ai_log_analysis")
logger.setLevel(logging.INFO)
logger.propagate = False
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(exist_ok=True)
log_path = log_dir / "application.log"
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
for handler in (logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8", delay=True)):
    handler.setFormatter(formatter)
    logger.addHandler(handler)

employees: dict[int, tuple[str, str, float]] = {
    101: ("Rahul", "IT", 50000.0),
    102: ("Priya", "HR", 60000.0),
}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Lab application started")
    yield
    logger.info("Lab application stopped")


app = FastAPI(title="AI Log Analysis Lab", lifespan=lifespan)


@app.get("/")
def home() -> dict[str, str]:
    logger.info("Home endpoint accessed")
    return {"message": "AI Log Analysis Demo is running"}


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("Application health check successful")
    return {"status": "ok"}


def find_employee(employee_id: int) -> tuple[str, str, float]:
    employee = employees.get(employee_id)
    if employee is None:
        logger.error("EmployeeNotFound: employee_id=%s", employee_id)
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int) -> dict[str, str]:
    name, department, _salary = find_employee(employee_id)
    logger.info("Employee %s fetched successfully", employee_id)
    return {"name": name, "department": department}


@app.get("/employees/{employee_id}/bonus")
def calculate_bonus(employee_id: int) -> dict[str, int | float]:
    _name, _department, salary = find_employee(employee_id)
    logger.info("Bonus calculated for employee_id=%s", employee_id)
    return {"employee_id": employee_id, "bonus": salary * 0.10}


@app.get("/demo-log-errors")
def generate_demo_errors() -> dict[str, str]:
    logger.error("DatabaseConnectionError: Unable to connect to database")
    logger.error("DatabaseConnectionError: Unable to connect to database")
    logger.warning("Slow database response: 8 seconds")
    logger.error("ValueError: Invalid employee salary value")
    logger.error("ValueError: Invalid employee salary value")
    logger.error("TimeoutError: External payment API request timed out")
    logger.error("TimeoutError: External payment API request timed out")
    logger.warning("Payment API response delayed")
    logger.error("DatabaseConnectionError: Unable to connect to database")
    logger.error("KeyError: Employee ID not found")
    logger.error("ZeroDivisionError: Division by zero")
    logger.warning("High API response time detected")
    logger.info("Demo error patterns generated")
    return {"message": "Demo log patterns written", "log_file": "logs/application.log"}


@app.post("/demo/database-error")
def demo_database_error() -> None:
    logger.warning("Simulated slow database response")
    logger.error("DatabaseConnectionError: Simulated database connection failure")
    raise HTTPException(status_code=503, detail="Simulated database unavailable")