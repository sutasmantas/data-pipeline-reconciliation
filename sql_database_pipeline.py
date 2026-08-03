"""Compatibility entry point retained from the selected GitHub foundation."""

from pipelineforge.sql_pipeline import SqlRunConfig, run_sql_incremental


def main() -> None:
    """Run the credential-free local SQL example."""

    _, info = run_sql_incremental(
        SqlRunConfig(
            source_url="sqlite:///.pipelineforge/source.sqlite3",
            table="orders",
            cursor_column="updated_at",
            initial_value="1970-01-01T00:00:00Z",
        )
    )
    print(info)


if __name__ == "__main__":
    main()
