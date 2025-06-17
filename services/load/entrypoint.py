#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrypoint for load service Docker Operator
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pytz

def run_load(target_date=None):
    """Run load for specific date"""
    if not target_date:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        yesterday = (datetime.now(jakarta_tz) - timedelta(days=1)).date()
        target_date = yesterday.strftime("%Y-%m-%d")
    
    # Import load logic
    from load_service import load_processed_data_to_final, generate_analytics_summary
    
    try:
        print(f"🚀 Starting load for date: {target_date}")
        
        # Load dari transform result
        transform_result_file = f"/shared/transform_result_{target_date}.json"
        if not os.path.exists(transform_result_file):
            raise FileNotFoundError(f"Transform result file not found: {transform_result_file}")
        
        # Load data ke final collection
        with open(transform_result_file, 'r', encoding='utf-8') as f:
            transform_result = json.load(f)
        
        json_file = transform_result.get('output_file')
        if not json_file:
            raise ValueError("No output file in transform result")
        
        load_result = load_processed_data_to_final(json_file, target_date)
        
        # Generate analytics
        analytics_result = generate_analytics_summary(target_date)
        
        # Save final result
        final_result = {
            "load_result": load_result,
            "analytics_result": analytics_result,
            "target_date": target_date,
            "completed_at": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat()
        }
        
        output_file = f"/shared/load_result_{target_date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Load completed. Result saved to: {output_file}")
        print(f"   Load result: {load_result}")
        print(f"   Analytics: {analytics_result.get('analytics', {})}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return 1

if __name__ == "__main__":
    # Ambil target_date dari argument atau environment variable
    target_date = os.getenv('TARGET_DATE')
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    exit_code = run_load(target_date)
    sys.exit(exit_code)
