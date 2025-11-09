#!/usr/bin/env python3
"""Quick test script for the agent with interactive and automated modes."""

import argparse
import os
import sys
from typing import Optional

from langgraph_agent import get_config, initialize_agent
from langgraph_agent.utils import get_workspace_client
from langgraph_agent.monitoring.logging import get_logger

# Set debug logging for this test
os.environ.setdefault("LOG_LEVEL", "DEBUG")

logger = get_logger(__name__)


# Default test queries
DEFAULT_TEST_QUERIES = [
    "What is 7 multiplied by 6 in Python?",
    "Calculate the 10th Fibonacci number",
    "What's the current time?",
]


def run_test_query(agent, query: str, show_details: bool = True) -> dict:
    """Run a single test query against the agent.

    Args:
        agent: The initialized agent
        query: Query to test
        show_details: Whether to show detailed output

    Returns:
        Response from the agent
    """
    if show_details:
        logger.info(f"Testing query: {query}")
        print("-" * 60)

    response = agent.predict({"input": [{"role": "user", "content": query}]})

    if show_details:
        print("\nResponse:")
        print(response)
        print("-" * 60)

    return response


def interactive_mode(agent):
    """Run agent in interactive mode for continuous testing.

    Args:
        agent: The initialized agent
    """
    logger.info("Entering interactive mode. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            query = input("\n👤 You: ").strip()

            if query.lower() in ["exit", "quit", "q"]:
                logger.info("Exiting interactive mode.")
                break

            if not query:
                continue

            print("\n🤖 Agent:")
            response = run_test_query(agent, query, show_details=False)
            print(response)

        except KeyboardInterrupt:
            logger.info("\n\nInterrupted by user. Exiting.")
            break
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)


def batch_mode(agent, queries: list[str]):
    """Run multiple test queries in batch mode.

    Args:
        agent: The initialized agent
        queries: List of queries to test
    """
    logger.info(f"Running {len(queries)} test queries...\n")

    results = []
    for i, query in enumerate(queries, 1):
        logger.info(f"\n[Test {i}/{len(queries)}]")
        try:
            response = run_test_query(agent, query)
            results.append({"query": query, "status": "success", "response": response})
        except Exception as e:
            logger.error(f"Failed: {e}")
            results.append({"query": query, "status": "failed", "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"Total: {len(results)} | Passed: {success_count} | Failed: {len(results) - success_count}")
    print("=" * 60)

    return results


def main():
    """Test the agent with configurable modes."""
    parser = argparse.ArgumentParser(
        description="Test the LangGraph MCP agent locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single query (default mode)
  python scripts/validate_agent.py

  # Custom single query
  python scripts/validate_agent.py --query "Calculate 15 * 23"

  # Interactive mode
  python scripts/validate_agent.py --interactive

  # Batch test mode
  python scripts/validate_agent.py --batch

  # Custom profile
  python scripts/validate_agent.py --profile production
        """,
    )
    parser.add_argument("--query", "-q", type=str, help="Single query to test (default: use first default query)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode for continuous testing")
    parser.add_argument("--batch", "-b", action="store_true", help="Run all default test queries in batch mode")
    parser.add_argument("--profile", "-p", type=str, help="Databricks CLI profile to use (default: from config)")

    args = parser.parse_args()

    try:
        logger.info("Loading configuration...")
        config = get_config()

        # Override profile if specified
        if args.profile:
            config.databricks.profile = args.profile

        logger.info(f"Initializing agent (profile: {config.databricks.profile})...")
        ws = get_workspace_client(config.databricks.profile)

        # Build MCP server URLs
        ws_host = ws.config.host
        managed_urls = config.mcp.managed_urls or [f"{ws_host}/api/2.0/mcp/functions/system/ai"]
        logger.debug(f"Managed MCP URLs: {managed_urls}")

        agent = initialize_agent(
            workspace_client=ws,
            llm_endpoint_name=config.model.endpoint_name,
            system_prompt=config.model.system_prompt,
            managed_mcp_urls=managed_urls,
            custom_mcp_urls=config.mcp.custom_urls,
        )

        logger.info("✓ Agent initialized!\n")

        # Choose mode
        if args.interactive:
            interactive_mode(agent)
        elif args.batch:
            batch_mode(agent, DEFAULT_TEST_QUERIES)
        else:
            # Single query mode
            query = args.query or DEFAULT_TEST_QUERIES[0]
            run_test_query(agent, query)

        logger.info("\n✓ Test complete!")
        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
