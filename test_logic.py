from logic import search_in_srts, get_video_url

print("Testing Search...")
# "Meryem" was seen in the file view
results = search_in_srts("Meryem", limit=2)
print(f"Found {len(results)} results.")
for r in results:
    print(r)
    url = get_video_url(r['filename'], r['seconds'])
    print(f"URL: {url}")

print("\nTesting Excel Link (Dummy)...")
# Test a known filename pattern if possible, or just rely on the above
# We'll just check if load_excel works implicitly via get_video_url above
