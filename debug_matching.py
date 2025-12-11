from logic import get_video_url, load_excel
import pandas as pd

# Mock the excel data if we can't read it, but let's try to read it first to see what's really there.
df = load_excel()
if df is not None:
    print("Excel loaded successfully.")
    print("Columns:", df.columns)
    print("First 10 titles in Excel:")
    # print(df['Title'].head(10)) # Causes encoding error on Windows console sometimes
    
    # Test cases that might fail
    filename_ep1 = "Kızıl Goncalar 1. Bölüm (FULL HD)_Turkish (auto-generated).srt"
    filename_ep31 = "Kızıl Goncalar 31. Bölüm (FULL HD)_Turkish (auto-generated).srt"
    
    print(f"\nTesting filename 1...")
    url_1 = get_video_url(filename_ep1, 0)
    print(f"Result URL for Ep 1: {url_1}")

    print(f"\nTesting filename 31...")
    url_31 = get_video_url(filename_ep31, 0)
    print(f"Result URL for Ep 31: {url_31}")

else:
    print("Could not load Excel file.")
