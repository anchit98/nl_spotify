# Phase 2: Storage, Standardization and Cleaning

This phase takes the raw data collected in Phase 1, cleans it, and stores it in a standardized format in the `clean` schema.

## Cleaning Steps
1. **Language Detection**: Only keeps English reviews.
2. **Emoji Filtering**: Removes any reviews containing emojis.
3. **Topic Filtering**: Ensures reviews cover specific discovery/recommendation topics.
4. **PII Masking**: Masks email addresses and phone numbers.
5. **Deduplication**: Removes exact duplicate texts.

## Setup
1. Run `sql/001_clean_schema.sql` in your Supabase SQL Editor.
2. Ensure `.env` is set up at the repository root.
3. Install dependencies:
   ```bash
   cd phase2-cleaning
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running
```bash
set PYTHONPATH=src
python -m phase2_cleaning.cleaner
```

## Next step

Phase 3 aggregates cleaned rows and synthesises answers to the six research questions. See [`../phase3-enrichment/README.md`](../phase3-enrichment/README.md).
