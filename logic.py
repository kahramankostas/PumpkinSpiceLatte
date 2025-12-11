import os
import re
import pandas as pd
import datetime

EXCEL_FILE = 'bolumler.xlsx'
SRT_FOLDER = 'srts'

def load_excel():
    """Validates that the Excel file exists."""
    if not os.path.exists(EXCEL_FILE):
        return None
    try:
        # We don't keep the dataframe open, just check if we can read it
        df = pd.read_excel(EXCEL_FILE)
        return df
    except Exception as e:
        print(f"Error reading excel: {e}")
        return None

def parse_timestamp(time_str):
    """Converts SRT timestamp (00:00:02,230) to seconds (float)."""
    # Format is HH:MM:SS,mmm
    try:
        time_str = time_str.replace(',', '.')
        h, m, s = time_str.split(':')
        seconds = float(h) * 3600 + float(m) * 60 + float(s)
        return int(seconds)
    except ValueError:
        return 0

def clean_text(text):
    """Removes standard SRT formatting tags if any."""
    clean = re.sub(r'<.*?>', '', text)
    clean = clean.replace('\n', ' ').strip()
    return clean

def search_in_srts(query, limit=None):
    """
    Searches for the query in all SRT files in the SRT_FOLDER.
    Returns a list of dicts: {'file': filename, 'time': timestamp_str, 'text': context, 'seconds': int}
    """
    results = []
    if not os.path.exists(SRT_FOLDER):
        return []
    
    query = query.lower()
    
    files = [f for f in os.listdir(SRT_FOLDER) if f.endswith('.srt')]
    
    for filename in files:
        filepath = os.path.join(SRT_FOLDER, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
             try:
                with open(filepath, 'r', encoding='latin-1') as f: # Fallback
                    content = f.read()
             except:
                 continue
                 
        # simpler parsing: split by double newlines or similar
        # A standard SRT block:
        # 1
        # 00:00:02,230 --> 00:00:04,640
        # Text
        
        blocks = content.split('\n\n')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # lines[0] is index, lines[1] is time, lines[2:] is text
                time_line = lines[1]
                if '-->' in time_line:
                    start_time = time_line.split('-->')[0].strip()
                    text_lines = " ".join(lines[2:])
                    text_clean = clean_text(text_lines)
                    
                    if query in text_clean.lower():
                        results.append({
                            'filename': filename,
                            'timestamp': start_time,
                            'text': text_clean,
                            'seconds': parse_timestamp(start_time)
                        })
                        
                        if limit and len(results) >= limit:
                            return results
    return results

def get_video_url(filename, seconds):
    """
    Finds the video URL for the given filename from the Excel file.
    Assumes filename contains the title or identifiable part.
    This logic needs to match how the Excel titles correspond to filenames.
    """
    df = load_excel()
    if df is None:
        return None
        
    # Heuristic: Try to match the numeric part or the main part of the filename
    # Filename ex: "Kızıl Goncalar 1. Bölüm (FULL HD)_Turkish (auto-generated).srt"
    # Excel Title ex: "1. Bölüm" or "Kızıl Goncalar 1. Bölüm"
    
    # Let's extract "1. Bölüm" or just the number "1"
    match = re.search(r'(\d+)\.\s*Bölüm', filename, re.IGNORECASE)
    episode_num = match.group(1) if match else None
    
    if not episode_num:
         # Fallback search by full string
         pass

    # normalize column names
    df.columns = [c.strip() for c in df.columns]
    
    found_url = None
    
    if episode_num:
        # Search in Title column for this number
        # Use regex with lookbehind to ensure we don't match "1" inside "31"
        # We look for: (not a digit) + episode_num + "."
        
        episode_num = str(int(episode_num)) # Ensure clean string '1' not '01'
        pattern = rf'(?<!\d){re.escape(episode_num)}\.\s*Bölüm'
        
        for index, row in df.iterrows():
            title = str(row['Title'])
            
            if re.search(pattern, title, re.IGNORECASE):
                found_url = row['Video url']
                break

    
    if found_url:
        # Append timestamp
        # YouTube format: &t=123s
        if 'youtube.com' in found_url or 'youtu.be' in found_url:
            separator = '&' if '?' in found_url else '?'
            return f"{found_url}{separator}t={seconds}s"
        else:
             return found_url # Return as is if not youtube or unknown format
             
    return None
