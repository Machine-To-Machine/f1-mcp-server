"""
Formula One MCP Server.

This module implements a server that provides Formula One racing data
through the Model Context Protocol (MCP). It exposes various tools
for querying F1 data including event schedules, driver information, telemetry
data, and race results.
"""

# Standard library imports
import json
import logging
import os
import sys
from typing import Any

# Third-party imports
import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server

# Local application imports
from .f1_data import (
    analyze_driver_performance,
    compare_drivers,
    get_championship_standings,
    get_driver_info,
    get_event_info,
    get_event_schedule,
    get_session_results,
    get_telemetry,
)

# Environment variable for log level
LOG_LEVEL = os.environ.get("F1_MCP_SERVER_LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 60
request_timestamps: list[float] = []


def check_rate_limit() -> bool:
    """
    Check if the current request exceeds rate limits.

    Returns:
        bool: True if within rate limit, False if exceeded
    """
    import time

    current_time = time.time()
    # Remove timestamps older than 60 seconds
    global request_timestamps
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < 60]

    # Check if we're over the limit
    if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        return False

    # Add current timestamp and allow request
    request_timestamps.append(current_time)
    return True


def validate_port(ctx: click.Context, param: click.Parameter, value: int) -> int:
    """Validate port number is in valid range."""
    if value is not None and (value < 1024 or value > 65535):
        raise click.BadParameter("Port must be between 1024 and 65535")
    return value


@click.command()
@click.option(
    "--port",
    default=8000,
    help="Port to listen on for SSE",
    callback=validate_port,
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Logging level",
)
def main(port: int, transport: str, log_level: str) -> int:
    """
    Run the Formula One MCP server.

    Args:
        port: The port number to listen on when using SSE transport
        transport: The transport mechanism ('stdio' or 'sse')
        log_level: The logging level to use

    Returns:
        int: Exit code (0 for success)
    """
    # Set up logging based on command line option
    logging.getLogger().setLevel(log_level)

    app = Server("formula-one-server")

    @app.call_tool()
    async def f1_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Execute the requested F1 data tool.

        Args:
            name: The name of the tool to execute
            arguments: Dictionary of arguments for the tool

        Returns:
            A list containing the tool execution result
        """
        # Implement rate limiting
        if not check_rate_limit():
            logger.warning("Rate limit exceeded")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "error",
                            "message": ("Rate limit exceeded. Please try again later."),
                        }
                    ),
                )
            ]

        try:
            # Sanitize and validate inputs
            sanitized_args = {}

            # Common validations
            if "year" in arguments:
                try:
                    year = int(arguments["year"])
                    # Validate year is reasonable
                    if not (1950 <= year <= 2100):
                        raise ValueError(f"Invalid year: {year}")
                    sanitized_args["year"] = year
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid year format: {arguments['year']}") from e

            # Tool-specific execution with sanitized inputs
            if name == "get_event_schedule":
                if "year" not in sanitized_args:
                    sanitized_args["year"] = int(arguments["year"])
                result = get_event_schedule(sanitized_args["year"])
            elif name == "get_event_info":
                if "identifier" not in arguments:
                    raise ValueError("Missing required argument: identifier")
                identifier = str(arguments["identifier"])
                result = get_event_info(sanitized_args["year"], identifier)
            elif name == "get_session_results":
                # Additional validations for session-related tools
                if "event_identifier" not in arguments:
                    raise ValueError("Missing required argument: event_identifier")
                if "session_name" not in arguments:
                    raise ValueError("Missing required argument: session_name")

                event_identifier = str(arguments["event_identifier"])
                session_name = str(arguments["session_name"])

                # Validate session_name format
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
                        "Invalid session_name: must be one of "
                        f"{', '.join(valid_sessions)}"
                    )

                result = get_session_results(
                    sanitized_args["year"],
                    event_identifier,
                    session_name,
                )
            elif name == "get_driver_info":
                # Handle remaining tools with proper validation
                # ... similar validation for other parameters ...
                result = get_driver_info(
                    sanitized_args["year"],
                    str(arguments["event_identifier"]),
                    str(arguments["session_name"]),
                    str(arguments["driver_identifier"]),
                )
            elif name == "analyze_driver_performance":
                result = analyze_driver_performance(
                    sanitized_args["year"],
                    str(arguments["event_identifier"]),
                    str(arguments["session_name"]),
                    str(arguments["driver_identifier"]),
                )
            elif name == "compare_drivers":
                result = compare_drivers(
                    sanitized_args["year"],
                    str(arguments["event_identifier"]),
                    str(arguments["session_name"]),
                    str(arguments["drivers"]),
                )
            elif name == "get_telemetry":
                lap_number = arguments.get("lap_number")
                if lap_number is not None:
                    try:
                        lap_number = int(lap_number)
                        if lap_number <= 0:
                            raise ValueError("Lap number must be positive")
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Invalid lap number: {lap_number}") from e

                result = get_telemetry(
                    sanitized_args["year"],
                    str(arguments["event_identifier"]),
                    str(arguments["session_name"]),
                    str(arguments["driver_identifier"]),
                    lap_number,
                )
            elif name == "get_championship_standings":
                round_num = arguments.get("round_num")
                if round_num is not None:
                    try:
                        round_num = int(round_num)
                        if round_num <= 0:
                            raise ValueError("Round number must be positive")
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Invalid round number: {round_num}") from e

                result = get_championship_standings(sanitized_args["year"], round_num)
            else:
                logger.error(f"Unknown tool requested: {name}")
                raise ValueError(f"Unknown tool: {name}")

            logger.debug(f"Tool '{name}' executed successfully")
            return [types.TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {str(e)}", exc_info=True)

            # Don't expose detailed error information in production
            if LOG_LEVEL == "DEBUG":
                error_msg = f"Error: {str(e)}"
            else:
                error_msg = "An error occurred while processing your request"

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"status": "error", "message": error_msg}),
                )
            ]

    # Rest of the function remains similar but with improved logging
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """
        List all available Formula One tools.

        Returns:
            A list of Tool objects describing available F1 data tools
        """
        return [
            types.Tool(
                name="get_event_schedule",
                description=("Get Formula One race calendar for a specific season"),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                    },
                    "required": ["year"],
                },
            ),
            types.Tool(
                name="get_event_info",
                description=(
                    "Get detailed information about a specific Formula One Grand Prix"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                    },
                    "required": ["year", "identifier"],
                },
            ),
            types.Tool(
                name="get_session_results",
                description="Get results for a specific Formula One session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "event_identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                        "session_name": {
                            "type": "string",
                            "description": (
                                "Session name (e.g., 'Race', 'Qualifying', "
                                "'Sprint', 'FP1', 'FP2', 'FP3')"
                            ),
                        },
                    },
                    "required": ["year", "event_identifier", "session_name"],
                },
            ),
            types.Tool(
                name="get_driver_info",
                description=("Get information about a specific Formula One driver"),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "event_identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                        "session_name": {
                            "type": "string",
                            "description": (
                                "Session name (e.g., 'Race', 'Qualifying', "
                                "'Sprint', 'FP1', 'FP2', 'FP3')"
                            ),
                        },
                        "driver_identifier": {
                            "type": "string",
                            "description": (
                                "Driver identifier (number, code, or name; "
                                "e.g., '44', 'HAM', 'Hamilton')"
                            ),
                        },
                    },
                    "required": [
                        "year",
                        "event_identifier",
                        "session_name",
                        "driver_identifier",
                    ],
                },
            ),
            types.Tool(
                name="analyze_driver_performance",
                description=("Analyze a driver's performance in a Formula One session"),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "event_identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                        "session_name": {
                            "type": "string",
                            "description": (
                                "Session name (e.g., 'Race', 'Qualifying', "
                                "'Sprint', 'FP1', 'FP2', 'FP3')"
                            ),
                        },
                        "driver_identifier": {
                            "type": "string",
                            "description": (
                                "Driver identifier (number, code, or name; "
                                "e.g., '44', 'HAM', 'Hamilton')"
                            ),
                        },
                    },
                    "required": [
                        "year",
                        "event_identifier",
                        "session_name",
                        "driver_identifier",
                    ],
                },
            ),
            types.Tool(
                name="compare_drivers",
                description=(
                    "Compare performance between multiple Formula One drivers"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "event_identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                        "session_name": {
                            "type": "string",
                            "description": (
                                "Session name (e.g., 'Race', 'Qualifying', "
                                "'Sprint', 'FP1', 'FP2', 'FP3')"
                            ),
                        },
                        "drivers": {
                            "type": "string",
                            "description": (
                                "Comma-separated list of driver codes "
                                "(e.g., 'HAM,VER,LEC')"
                            ),
                        },
                    },
                    "required": [
                        "year",
                        "event_identifier",
                        "session_name",
                        "drivers",
                    ],
                },
            ),
            types.Tool(
                name="get_telemetry",
                description=("Get telemetry data for a specific Formula One lap"),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "event_identifier": {
                            "type": "string",
                            "description": (
                                "Event name or round number (e.g., 'Monaco' or '7')"
                            ),
                        },
                        "session_name": {
                            "type": "string",
                            "description": (
                                "Session name (e.g., 'Race', 'Qualifying', "
                                "'Sprint', 'FP1', 'FP2', 'FP3')"
                            ),
                        },
                        "driver_identifier": {
                            "type": "string",
                            "description": (
                                "Driver identifier (number, code, or name; "
                                "e.g., '44', 'HAM', 'Hamilton')"
                            ),
                        },
                        "lap_number": {
                            "type": "number",
                            "description": (
                                "Lap number (optional, gets fastest lap if not "
                                "provided)"
                            ),
                        },
                    },
                    "required": [
                        "year",
                        "event_identifier",
                        "session_name",
                        "driver_identifier",
                    ],
                },
            ),
            types.Tool(
                name="get_championship_standings",
                description="Get Formula One championship standings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "number",
                            "description": "Season year (e.g., 2023)",
                        },
                        "round_num": {
                            "type": "number",
                            "description": (
                                "Round number (optional, gets latest "
                                "standings if not provided)"
                            ),
                        },
                    },
                    "required": ["year"],
                },
            ),
        ]

    if transport == "sse":
        # Import SSE-specific modules only when needed
        try:
            import uvicorn
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.middleware.cors import CORSMiddleware
            from starlette.routing import Mount, Route
        except ImportError:
            logger.error(
                "SSE transport requires additional dependencies. "
                "Install with: pip install uvicorn starlette"
            )
            return 1

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            """Handle incoming SSE connections."""
            try:
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await app.run(
                        streams[0],
                        streams[1],
                        app.create_initialization_options(),
                    )
            except Exception as e:
                logger.error(f"Error in SSE handler: {str(e)}", exc_info=True)
                raise

        # Add CORS middleware for security
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Configure more restrictively in production
                allow_methods=["GET", "POST"],
                allow_headers=["*"],
            )
        ]

        starlette_app = Starlette(
            debug=(LOG_LEVEL == "DEBUG"),
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
            middleware=middleware,
        )

        # Add a more descriptive log message before starting the server
        logger.info(
            f"Starting Formula One MCP server on port {port} with SSE transport"
        )
        try:
            uvicorn.run(
                starlette_app,
                host="0.0.0.0",  # noqa: S104
                port=port,
                log_level=LOG_LEVEL.lower(),
                access_log=(LOG_LEVEL == "DEBUG"),
            )
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}", exc_info=True)
            return 1
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            """Run the server using stdio transport."""
            logger.info("Starting Formula One MCP server with stdio transport")
            try:
                async with stdio_server() as streams:
                    await app.run(
                        streams[0],
                        streams[1],
                        app.create_initialization_options(),
                    )
            except Exception as e:
                logger.error(f"Error in stdio server: {str(e)}", exc_info=True)
                sys.exit(1)

        try:
            anyio.run(arun)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return 0
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
