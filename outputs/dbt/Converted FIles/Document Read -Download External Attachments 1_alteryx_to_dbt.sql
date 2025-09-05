```sql
-- dbt model to extract SAP document attachment URLs and filenames

{{ config(materialized='table') }}

WITH source_sap_documents AS (

    SELECT 
        'FOL18          4 URL48000000000001' AS document_id, -- Replace with your actual document ID source
        'URL48000000000001.URL' AS filename, -- Replace with your actual filename source or logic
        'http://example.com/path/to/attachment?KEY=somekey' AS xstring -- Replace with your actual xstring source (URL)

),

cleaned_sap_documents AS (

    SELECT 
        document_id,
        REPLACE(filename, '.URL', '') AS filename, -- Remove .URL extension
        REPLACE(xstring, '&KEY&', '') AS url -- Remove &KEY& from the URL

    FROM source_sap_documents

)


SELECT * FROM cleaned_sap_documents

```