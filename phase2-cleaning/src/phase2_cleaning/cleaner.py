import sys
import traceback
from tqdm import tqdm

from phase2_cleaning.config import Settings
from phase2_cleaning.db import Database
from phase2_cleaning.filters import clean_text, has_emoji, is_english, get_matched_topics

def run_cleaning() -> None:
    settings = Settings.from_env()
    db = Database(settings)
    
    run_id = db.start_run()
    total_processed = 0
    total_kept = 0
    
    try:
        while True:
            raw_items = db.get_unprocessed_raw_items(batch_size=500)
            if not raw_items:
                break
                
            kept_items = []
            processed_records = []
            
            for raw in raw_items:
                raw_id = raw["id"]
                payload = raw.get("raw_payload", {})
                text = payload.get("text", "")
                
                # 1. Emoji check
                if has_emoji(text):
                    processed_records.append({
                        "raw_id": raw_id,
                        "kept": False,
                        "drop_reason": "contains_emoji"
                    })
                    continue
                    
                # 2. Language check
                if not is_english(text):
                    processed_records.append({
                        "raw_id": raw_id,
                        "kept": False,
                        "drop_reason": "not_english"
                    })
                    continue
                    
                # 3. Topic filtering
                matched_topics = get_matched_topics(text)
                if not matched_topics:
                    processed_records.append({
                        "raw_id": raw_id,
                        "kept": False,
                        "drop_reason": "no_relevant_topics"
                    })
                    continue
                    
                # 4. Clean text (PII masking, whitespace)
                cleaned_text = clean_text(text)
                if not cleaned_text:
                    processed_records.append({
                        "raw_id": raw_id,
                        "kept": False,
                        "drop_reason": "empty_after_cleaning"
                    })
                    continue
                    
                # Keep item
                payload = raw.get("raw_payload", {})
                kept_items.append({
                    "raw_id": raw_id,
                    "source": raw["source"],
                    "source_item_id": raw["source_item_id"],
                    "posted_at": raw.get("posted_at"),
                    "cleaned_text": cleaned_text,
                    "rating": payload.get("rating"),
                    "language": "en",
                    "country": payload.get("country"),
                    "user_hints": payload.get("user_hints"),
                    "topics_matched": matched_topics
                })
                
                processed_records.append({
                    "raw_id": raw_id,
                    "kept": True,
                    "drop_reason": None
                })
                
            db.save_cleaned_items(kept_items, processed_records)
            
            total_processed += len(raw_items)
            total_kept += len(kept_items)
            print(f"Processed {total_processed} items... (Kept: {total_kept})")
            
        db.finish_run(run_id, "success", total_processed, total_kept)
        print(f"Cleaning complete. Processed: {total_processed}, Kept: {total_kept}")
        
    except Exception as exc:
        err = traceback.format_exc()
        db.finish_run(run_id, "failed", total_processed, total_kept, error_message=err)
        print(f"Cleaning failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_cleaning()
