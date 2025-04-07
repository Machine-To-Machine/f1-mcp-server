"""
Formula One Data Processing Module.

This module provides functions for accessing and processing Formula One racing
data through the FastF1 API. It includes functionality for retrieving event
schedules, session results, driver information, telemetry data, and
championship standings.

All functions follow a consistent pattern of returning structured JSON-
compatible responses with appropriate error handling.
"""

# Standard library imports
import logging
import os
import tempfile
from datetime import datetime
from typing import Any

# Third-party imports
import fastf1
import numpy as np
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# Configure FastF1 cache with proper path security and isolation
# Use a temporary directory to avoid permission issues and provide isolation
CACHE_DIR = os.path.join(tempfile.gettempdir(), "f1-cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Apply proper permissions to the cache directory
try:
    os.chmod(CACHE_DIR, 0o700)  # Restrict to current user
except Exception as e:
    logger.warning(f"Failed to set permissions on cache directory: {str(e)}")

fastf1.Cache.enable_cache(CACHE_DIR)

# Set a maximum limit for data size to prevent excessive memory usage
MAX_TELEMETRY_POINTS = 5000


def json_serial(obj: Any) -> str | int | float | None:
    """
    Convert non-JSON serializable objects to strings.

    Args:
        obj: Object to be serialized to JSON

    Returns:
        JSON serializable representation of the object
    """
    if isinstance(obj, datetime | pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if pd.isna(obj) or obj is None:
        return None
    return str(obj)


def validate_year(year: Any) -> int:
    """
    Validate that the provided year is valid for F1 data.

    Args:
        year: Year value to validate

    Returns:
        Valid year as integer

    Raises:
        ValueError: If year is invalid
    """
    try:
        year_int = int(year)
        # F1 started in 1950 and we don't want future years far ahead
        current_year = datetime.now().year
        if year_int < 1950 or year_int > current_year + 1:
            raise ValueError(f"Year must be between 1950 and {current_year + 1}")
        return year_int
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid year format: {year}") from e


def get_event_schedule(year: Any) -> dict[str, Any]:
    """
    Get the event schedule for a specified Formula One season.

    Args:
        year (int or str): The year of the F1 season

    Returns:
        dict: Status and schedule data or error information
    """
    try:
        # Validate year
        year_int = validate_year(year)

        logger.debug(f"Fetching event schedule for {year_int}")
        schedule = fastf1.get_event_schedule(year_int)

        # Convert DataFrame to JSON serializable format
        result = []
        for _, row in schedule.iterrows():
            event_dict = row.to_dict()
            # Clean and convert non-serializable values
            clean_dict = {k: json_serial(v) for k, v in event_dict.items()}
            result.append(clean_dict)

        logger.info(f"Successfully retrieved {len(result)} events for {year_int}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error retrieving event schedule: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to retrieve event schedule: {str(e)}",
        }


def get_event_info(year: Any, identifier: str) -> dict[str, Any]:
    """
    Get information about a specific Formula One event.

    Args:
        year (int or str): The year of the F1 season
        identifier (str): Event name or round number

    Returns:
        dict: Status and event data or error information
    """
    try:
        # Validate year
        year_int = validate_year(year)

        # Validate identifier
        if not identifier or not isinstance(identifier, str | int):
            raise ValueError("Invalid event identifier")

        logger.debug(f"Fetching event info for {year_int}, event: {identifier}")

        # Identifier can be event name or round number
        if str(identifier).isdigit():
            event = fastf1.get_event(year_int, int(identifier))
        else:
            event = fastf1.get_event(year_int, str(identifier))

        # Convert Series to dict and clean non-serializable values
        event_dict = event.to_dict()
        clean_dict = {k: json_serial(v) for k, v in event_dict.items()}

        logger.info(
            f"Successfully retrieved event info for {year_int}, event: {identifier}"
        )
        return {"status": "success", "data": clean_dict}
    except Exception as e:
        logger.error(f"Error retrieving event info: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to retrieve event information: {str(e)}",
        }


def get_session_results(
    year: Any, event_identifier: str, session_name: str
) -> dict[str, Any]:
    """
    Get results for a specific Formula One session.

    Args:
        year (int or str): The year of the F1 season
        event_identifier (str): Event name or round number
        session_name (str): Session type (Race, Qualifying, Sprint, etc.)

    Returns:
        dict: Status and session results data or error information
    """
    try:
        # Validate year
        year_int = validate_year(year)

        # Validate session name
        valid_sessions = [
            "Race",
            "Qualifying",
            "Sprint",
            "FP1",
            "FP2",
            "FP3",
            "SprintQualifying",
        ]
        if session_name not in valid_sessions:
            raise ValueError(
                f"Invalid session name. Must be one of: {', '.join(valid_sessions)}"
            )

        logger.debug(
            f"Fetching session results for {year_int}, "
            f"event: {event_identifier}, session: {session_name}"
        )

        session = fastf1.get_session(year_int, event_identifier, session_name)
        # Load session without telemetry for faster results
        session.load(telemetry=False)

        # Get results as a DataFrame
        results = session.results

        # Convert results to JSON serializable format
        result_list = []
        for _, result in results.items():
            driver_result = result.to_dict()
            # Clean and convert non-serializable values
            clean_dict = {k: json_serial(v) for k, v in driver_result.items()}
            result_list.append(clean_dict)

        logger.info(
            f"Successfully retrieved results for {year_int}, "
            f"event: {event_identifier}, session: {session_name}"
        )
        return {"status": "success", "data": result_list}
    except Exception as e:
        logger.error(f"Error retrieving session results: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to retrieve session results: {str(e)}",
        }


def get_driver_info(
    year: Any, event_identifier: str, session_name: str, driver_identifier: str
) -> dict[str, Any]:
    """
    Get information about a specific Formula One driver.

    Args:
        year (int or str): The year of the F1 season
        event_identifier (str): Event name or round number
        session_name (str): Session type (Race, Qualifying, Sprint, etc.)
        driver_identifier (str): Driver number, code, or name

    Returns:
        dict: Status and driver information or error information
    """
    try:
        # Validate year
        year_int = validate_year(year)

        logger.debug(
            f"Fetching driver info for {year_int}, "
            f"event: {event_identifier}, session: {session_name}, "
            f"driver: {driver_identifier}"
        )
        session = fastf1.get_session(year_int, event_identifier, session_name)
        # Load session without telemetry for faster results
        session.load(telemetry=False)

        driver_info = session.get_driver(driver_identifier)

        # Convert to JSON serializable format
        driver_dict = driver_info.to_dict()
        clean_dict = {k: json_serial(v) for k, v in driver_dict.items()}

        logger.info(f"Successfully retrieved driver info for {driver_identifier}")
        return {"status": "success", "data": clean_dict}
    except Exception as e:
        logger.error(f"Error retrieving driver info: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to retrieve driver information: {str(e)}",
        }


def analyze_driver_performance(
    year: Any, event_identifier: str, session_name: str, driver_identifier: str
) -> dict[str, Any]:
    """
    Analyze a driver's performance in a Formula One session.

    Args:
        year (int or str): The year of the F1 season
        event_identifier (str): Event name or round number
        session_name (str): Session type (Race, Qualifying, Sprint, etc.)
        driver_identifier (str): Driver number, code, or name

    Returns:
        dict: Status and performance analysis or error information
    """
    try:
        # Validate year
        year_int = validate_year(year)

        logger.debug(
            f"Analyzing driver performance for {year_int}, "
            f"event: {event_identifier}, session: {session_name}, "
            f"driver: {driver_identifier}"
        )
        session = fastf1.get_session(year_int, event_identifier, session_name)
        session.load()

        # Get laps for the specified driver
        driver_laps = session.laps.pick_driver(driver_identifier)

        if len(driver_laps) == 0:
            return {
                "status": "error",
                "message": f"No laps found for driver {driver_identifier}",
            }

        # Basic statistics
        fastest_lap = driver_laps.pick_fastest()

        # Calculate average lap time (excluding outliers)
        valid_lap_times = []
        for _, lap in driver_laps.iterrows():
            if lap["LapTime"] is not None and not pd.isna(lap["LapTime"]):
                valid_lap_times.append(lap["LapTime"].total_seconds())

        avg_lap_time = (
            sum(valid_lap_times) / len(valid_lap_times) if valid_lap_times else None
        )

        # Format lap time as minutes:seconds.milliseconds
        formatted_fastest = (
            str(fastest_lap["LapTime"])
            if fastest_lap is not None and not pd.isna(fastest_lap["LapTime"])
            else None
        )

        # Get all lap times - limit to avoid excessive data
        max_laps = min(len(driver_laps), 100)  # Safety limit
        lap_times = []

        for _, lap in driver_laps.iloc[:max_laps].iterrows():
            lap_dict = {
                "LapNumber": int(lap["LapNumber"])
                if not pd.isna(lap["LapNumber"])
                else None,
                "LapTime": str(lap["LapTime"]) if not pd.isna(lap["LapTime"]) else None,
                "Compound": lap["Compound"] if not pd.isna(lap["Compound"]) else None,
                "TyreLife": int(lap["TyreLife"])
                if not pd.isna(lap["TyreLife"])
                else None,
                "Stint": int(lap["Stint"]) if not pd.isna(lap["Stint"]) else None,
                "FreshTyre": bool(lap["FreshTyre"])
                if not pd.isna(lap["FreshTyre"])
                else None,
                "LapStartTime": json_serial(lap["LapStartTime"])
                if not pd.isna(lap["LapStartTime"])
                else None,
            }
            lap_times.append(lap_dict)

        # Format results
        result = {
            "DriverCode": fastest_lap["Driver"]
            if fastest_lap is not None and not pd.isna(fastest_lap["Driver"])
            else None,
            "TotalLaps": len(driver_laps),
            "FastestLap": formatted_fastest,
            "AverageLapTime": avg_lap_time,
            "LapTimes": lap_times,
        }

        logger.info(f"Successfully analyzed performance for driver {driver_identifier}")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def compare_drivers(year, event_identifier, session_name, drivers):
    """
    Compare performance between multiple Formula One drivers.

    Args:
        year (int or str): The year of the F1 season
        event_identifier (str): Event name or round number
        session_name (str): Session type (Race, Qualifying, Sprint, etc.)
        drivers (str): Comma-separated list of driver codes

    Returns:
        dict: Status and driver comparison data or error information
    """
    try:
        year = int(year)
        drivers_list = drivers.split(",")

        session = fastf1.get_session(year, event_identifier, session_name)
        session.load()

        driver_comparisons = []

        for driver in drivers_list:
            # Get laps and fastest lap for each driver
            driver_laps = session.laps.pick_driver(driver)
            fastest_lap = driver_laps.pick_fastest()

            # Calculate average lap time
            valid_lap_times = []
            for _, lap in driver_laps.iterrows():
                if lap["LapTime"] is not None and not pd.isna(lap["LapTime"]):
                    valid_lap_times.append(lap["LapTime"].total_seconds())

            avg_lap_time = (
                sum(valid_lap_times) / len(valid_lap_times) if valid_lap_times else None
            )

            # Format lap time as string
            formatted_fastest = None
            fastest_lap_number = None
            if fastest_lap is not None:
                formatted_fastest = (
                    str(fastest_lap["LapTime"])
                    if not pd.isna(fastest_lap["LapTime"])
                    else None
                )
                fastest_lap_number = (
                    int(fastest_lap["LapNumber"])
                    if not pd.isna(fastest_lap["LapNumber"])
                    else None
                )

            # Compile driver data
            driver_data = {
                "DriverCode": driver,
                "FastestLap": formatted_fastest,
                "FastestLapNumber": fastest_lap_number,
                "TotalLaps": len(driver_laps),
                "AverageLapTime": avg_lap_time,
            }

            driver_comparisons.append(driver_data)

        return {"status": "success", "data": driver_comparisons}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_telemetry(
    year, event_identifier, session_name, driver_identifier, lap_number=None
):
    """
    Get telemetry data for a specific lap or fastest lap.

    Args:
        year (int or str): The year of the F1 season
        event_identifier (str): Event name or round number
        session_name (str): Session type (Race, Qualifying, Sprint, etc.)
        driver_identifier (str): Driver number, code, or name
        lap_number (int, optional): Specific lap number or None for fastest lap

    Returns:
        dict: Status and telemetry data or error information
    """
    try:
        year = int(year)
        session = fastf1.get_session(year, event_identifier, session_name)
        session.load()

        # Get laps for the specified driver
        driver_laps = session.laps.pick_driver(driver_identifier)

        if len(driver_laps) == 0:
            return {
                "status": "error",
                "message": f"No laps found for driver {driver_identifier}",
            }

        # Get the specific lap or fastest lap
        if lap_number:
            matching_laps = driver_laps[driver_laps["LapNumber"] == int(lap_number)]
            if len(matching_laps) == 0:
                return {
                    "status": "error",
                    "message": (
                        f"Lap number {lap_number} not found for driver "
                        f"{driver_identifier}"
                    ),
                }
            lap = matching_laps.iloc[0]
        else:
            lap = driver_laps.pick_fastest()
            if lap is None:
                return {
                    "status": "error",
                    "message": "No valid fastest lap found for driver "
                    f"{driver_identifier}",
                }

        # Get telemetry data
        telemetry = lap.get_telemetry()

        # Convert to JSON serializable format
        telemetry_dict = telemetry.to_dict(orient="records")
        clean_data = []

        for item in telemetry_dict:
            clean_item = {k: json_serial(v) for k, v in item.items()}
            clean_data.append(clean_item)

        # Add lap information
        lap_info = {
            "LapNumber": int(lap["LapNumber"])
            if not pd.isna(lap["LapNumber"])
            else None,
            "LapTime": str(lap["LapTime"]) if not pd.isna(lap["LapTime"]) else None,
            "Compound": lap["Compound"] if not pd.isna(lap["Compound"]) else None,
            "TyreLife": int(lap["TyreLife"]) if not pd.isna(lap["TyreLife"]) else None,
        }

        result = {"lapInfo": lap_info, "telemetry": clean_data}

        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_championship_standings(year, round_num=None):
    """
    Get championship standings for drivers and constructors.

    Args:
        year (int or str): The year of the F1 season
        round_num (int, optional): Specific round number or None for latest

    Returns:
        dict: Status and championship standings or error information
    """
    try:
        year = int(year)

        # Create Ergast API client
        ergast = fastf1.ergast.Ergast()

        # Get Ergast API data
        if round_num:
            round_num = int(round_num)  # Ensure proper type conversion
            drivers_standings = ergast.get_driver_standings(
                season=year, round=round_num
            ).content[0]
            constructor_standings = ergast.get_constructor_standings(
                season=year, round=round_num
            ).content[0]
        else:
            drivers_standings = ergast.get_driver_standings(season=year).content[0]
            constructor_standings = ergast.get_constructor_standings(
                season=year
            ).content[0]

        # Convert driver standings to JSON serializable format
        drivers_list = []
        for _, row in drivers_standings.iterrows():
            driver_dict = row.to_dict()
            clean_dict = {k: json_serial(v) for k, v in driver_dict.items()}
            drivers_list.append(clean_dict)

        # Convert constructor standings to JSON serializable format
        constructors_list = []
        for _, row in constructor_standings.iterrows():
            constructor_dict = row.to_dict()
            clean_dict = {k: json_serial(v) for k, v in constructor_dict.items()}
            constructors_list.append(clean_dict)

        return {
            "status": "success",
            "data": {
                "drivers": drivers_list,
                "constructors": constructors_list,
            },
        }
    except Exception as e:
        logger.error(f"Error analyzing driver performance: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Failed to analyze driver performance: {str(e)}",
        }
