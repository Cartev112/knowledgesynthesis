#!/usr/bin/env python3
"""
Test script for the async ingestion system.
This script tests the complete flow from job submission to completion.
"""

import requests
import time
import json
import sys

# Configuration
API_BASE = "http://localhost:8000"
TEST_TEXT = """
This is a test document about machine learning and artificial intelligence.
Machine learning is a subset of artificial intelligence that focuses on algorithms.
Deep learning uses neural networks with multiple layers.
Natural language processing helps computers understand human language.
Computer vision enables machines to interpret visual information.
"""

def test_text_ingestion():
    """Test async text ingestion."""
    print("🧪 Testing async text ingestion...")
    
    # Submit job
    payload = {
        "text": TEST_TEXT,
        "document_title": "Test Document",
        "user_id": "test_user",
        "user_first_name": "Test",
        "user_last_name": "User",
        "max_relationships": 10
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/ingest/text_async", json=payload)
        response.raise_for_status()
        
        result = response.json()
        job_id = result["job_id"]
        print(f"✅ Job submitted successfully: {job_id}")
        
        # Poll for completion
        print("⏳ Polling for job completion...")
        max_attempts = 60  # 1 minute max
        attempts = 0
        
        while attempts < max_attempts:
            time.sleep(1)
            attempts += 1
            
            status_response = requests.get(f"{API_BASE}/api/ingest/job/{job_id}")
            status_response.raise_for_status()
            
            job_status = status_response.json()
            print(f"   Status: {job_status['status']} (attempt {attempts})")
            
            if job_status["status"] == "completed":
                print(f"✅ Job completed successfully!")
                print(f"   Document ID: {job_status.get('document_id')}")
                print(f"   Document Title: {job_status.get('document_title')}")
                print(f"   Triplets Extracted: {job_status.get('triplets_extracted')}")
                print(f"   Triplets Written: {job_status.get('triplets_written')}")
                return True
            elif job_status["status"] == "failed":
                print(f"❌ Job failed: {job_status.get('error_message')}")
                return False
        
        print("⏰ Job timed out")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_job_listing():
    """Test job listing endpoint."""
    print("\n🧪 Testing job listing...")
    
    try:
        response = requests.get(f"{API_BASE}/api/ingest/jobs?limit=10")
        response.raise_for_status()
        
        result = response.json()
        jobs = result["jobs"]
        
        print(f"✅ Found {len(jobs)} jobs")
        for job in jobs[:3]:  # Show first 3
            print(f"   - {job['job_id']}: {job['status']} ({job.get('document_title', 'No title')})")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def check_services():
    """Check if required services are running."""
    print("🔍 Checking services...")
    
    services = [
        ("FastAPI", f"{API_BASE}/health"),
        ("RabbitMQ Management", "http://localhost:15672"),
    ]
    
    all_ok = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: Responding but status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ {name}: Not accessible at {url}")
            all_ok = False
    
    return all_ok

def main():
    """Run all tests."""
    print("=" * 60)
    print("Knowledge Synthesis - Async Ingestion Test")
    print("=" * 60)
    
    # Check services
    if not check_services():
        print("\n❌ Some services are not running. Please start:")
        print("   1. docker-compose up -d")
        print("   2. python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print("   3. python -m app.worker")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Run tests
    tests = [
        ("Text Ingestion", test_text_ingestion),
        ("Job Listing", test_job_listing),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Async ingestion system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

