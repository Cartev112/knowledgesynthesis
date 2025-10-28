#!/usr/bin/env python3
"""
Migration script to link entities to workspaces.
Run this after deploying the workspace linking fixes.
"""

import requests
import sys

# Update this to your Railway URL
RAILWAY_URL = input("Enter your Railway app URL (e.g., https://your-app.railway.app): ").strip()

if not RAILWAY_URL:
    print("Error: Railway URL is required")
    sys.exit(1)

# Remove trailing slash if present
RAILWAY_URL = RAILWAY_URL.rstrip('/')

print(f"\n🔍 Checking workspace link status...")
print(f"URL: {RAILWAY_URL}/api/migrate/check-workspace-links")

try:
    # First, check the current status
    check_response = requests.get(
        f"{RAILWAY_URL}/api/migrate/check-workspace-links",
        timeout=30
    )
    
    if check_response.status_code == 200:
        status = check_response.json()
        print("\n📊 Current Status:")
        print(f"  Documents: {status['documents']['total']} total, {status['documents']['linked_to_workspace']} linked, {status['documents']['unlinked']} unlinked")
        print(f"  Entities: {status['entities']['total']} total, {status['entities']['linked_to_workspace']} linked, {status['entities']['unlinked']} unlinked")
        
        if status['entities']['unlinked'] == 0:
            print("\n✅ All entities are already linked to workspaces!")
            sys.exit(0)
        
        print(f"\n⚠️  Found {status['entities']['unlinked']} unlinked entities")
        
    elif check_response.status_code == 401:
        print("\n❌ Authentication required. This endpoint requires login.")
        print("Please run this migration from your browser's console or use authenticated requests.")
        print("\nBrowser Console Method:")
        print("1. Log into your app")
        print("2. Open browser DevTools (F12)")
        print("3. Go to Console tab")
        print("4. Run:")
        print(f"   fetch('{RAILWAY_URL}/api/migrate/link-entities-to-workspaces', {{method: 'POST'}}).then(r => r.json()).then(console.log)")
        sys.exit(1)
    else:
        print(f"\n❌ Check failed with status {check_response.status_code}")
        print(check_response.text)
        sys.exit(1)
    
    # Ask for confirmation
    confirm = input("\n🚀 Run migration to link entities to workspaces? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    print("\n🔄 Running migration...")
    print(f"URL: {RAILWAY_URL}/api/migrate/link-entities-to-workspaces")
    
    # Run the migration
    migrate_response = requests.post(
        f"{RAILWAY_URL}/api/migrate/link-entities-to-workspaces",
        timeout=60
    )
    
    if migrate_response.status_code == 200:
        result = migrate_response.json()
        print("\n✅ Migration completed successfully!")
        print(f"  Entities linked: {result.get('entities_linked', 0)}")
        print(f"  Workspaces affected: {result.get('workspaces_affected', 0)}")
        print(f"  Message: {result.get('message', 'Done')}")
    elif migrate_response.status_code == 401:
        print("\n❌ Authentication required. This endpoint requires login.")
        print("Please run this migration from your browser's console:")
        print(f"fetch('{RAILWAY_URL}/api/migrate/link-entities-to-workspaces', {{method: 'POST'}}).then(r => r.json()).then(console.log)")
    else:
        print(f"\n❌ Migration failed with status {migrate_response.status_code}")
        print(migrate_response.text)
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print(f"\n❌ Could not connect to {RAILWAY_URL}")
    print("Please check that:")
    print("  1. The URL is correct")
    print("  2. The server is running")
    print("  3. You have internet connection")
    sys.exit(1)
except requests.exceptions.Timeout:
    print("\n❌ Request timed out")
    print("The server might be slow or unresponsive")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    sys.exit(1)
