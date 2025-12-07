"""
Quick test script to verify API functionality

This is a minimal test to check if the API is working.
Run this after starting the server to verify everything is set up correctly.
"""

import requests
import sys


API_BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("Testing health check...", end=" ")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print("✅ PASSED")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...", end=" ")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("name") == "FrameShift API":
                print("✅ PASSED")
                return True
        print(f"❌ FAILED: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_docs():
    """Test docs endpoint"""
    print("Testing docs endpoint...", end=" ")
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ PASSED")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_list_runs():
    """Test list runs endpoint"""
    print("Testing list runs...", end=" ")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/runs")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASSED (found {data.get('total', 0)} runs)")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("FrameShift API Quick Test")
    print("="*60 + "\n")
    
    print("Make sure the server is running:")
    print("  python -m api.main")
    print("  OR")
    print("  uvicorn api.main:app --reload")
    print()
    
    tests = [
        test_health,
        test_root,
        test_docs,
        test_list_runs
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! API is working correctly.")
        print("\nNext steps:")
        print("  - View API docs: http://localhost:8000/docs")
        print("  - Run full example: python api/examples/client_example.py")
    else:
        print("❌ Some tests failed. Check if the server is running.")
        sys.exit(1)
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

