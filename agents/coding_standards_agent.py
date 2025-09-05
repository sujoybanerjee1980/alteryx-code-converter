def pyspark_coding_standards():
    pyspark_standards = """
        General Python (PEP 8) Standards for Pyspark:

        Indentation: 4 spaces.
        Line Length: ≤ 79 characters.
        Imports: Top of file, one per line, no wildcard imports.
        Whitespace: Consistent spacing.
        Naming: snake_case (vars, funcs), CamelCase (classes), CONSTANT_CASE (constants).
        Comments: Clear and concise.

        PySpark:
        Lazy Evaluation: Chain transformations, use actions sparingly.
        Avoid collect(): Use alternatives for large datasets.
        Caching: Use cache()/persist() for frequently accessed data.
        Error Handling: Robust error handling for distributed operations.
        UDFs: Prioritize built-in Spark functions; use Pandas UDFs if needed.
        If there is no proper transformation in PySpark, Give in python with commented code.
        
    """
    return pyspark_standards


def dbt_coding_standards():
    dbt_standards = """
        1. Project Structure

        Consistent Naming: Use descriptive names for models (e.g., stg_source_table, dim_dimension, fct_fact).  Pluralize model names.
        Primary Keys: Name primary keys  object_id, use string data type.
        Column Naming: Use snake_case. Prefix booleans with is_ or has_. Timestamps: event_at (UTC); Dates: event_date.     
        Business Terms: Use business names, not source system names.


        2. SQL Style

        Modular Queries: Break large queries into smaller, reusable models.
        Data Sources: Use sources for raw data, refs for other dbt models.
        CTEs: Use CTEs for readability and complex logic.
        Formatting: Use SQL formatter (like SQLFluff) for consistent code.

    """
    return dbt_standards