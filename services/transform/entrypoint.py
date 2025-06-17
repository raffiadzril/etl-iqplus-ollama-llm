#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrypoint for transform service Docker Operator
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pytz

def run_transform(target_date=None):
    """Run transformation for specific date"""
    if not target_date:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        yesterday = (datetime.now(jakarta_tz) - timedelta(days=1)).date()
        target_date = yesterday.strftime("%Y-%m-%d")
    
    # Import transform logic
    from transform_service import process_news_with_llm
    
    try:
        print(f"🚀 Starting transformation for date: {target_date}")
        
        # Jalankan transform
        result = process_news_with_llm(target_date)
        
        # Save hasil ke file untuk komunikasi antar container
        output_file = f"/shared/transform_result_{target_date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Transform completed. Result saved to: {output_file}")
        print(f"   Articles processed: {result.get('articles_processed', 0)}")
        print(f"   Output file: {result.get('output_file', '')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Transform failed: {e}")
        return 1

if __name__ == "__main__":
    # Ambil target_date dari argument atau environment variable
    target_date = os.getenv('TARGET_DATE')
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    exit_code = run_transform(target_date)
    sys.exit(exit_code)
