"""Compatibility import for the GitHub foundation's SQL source.

The upstream demo carried an early copy of this source. Current dlt owns and
tests the same responsibility, so PipelineForge preserves the original import
path while delegating to dlt 1.29.1 instead of maintaining the old fork.
"""

from dlt.sources.sql_database import sql_database, sql_table

__all__ = ["sql_database", "sql_table"]
