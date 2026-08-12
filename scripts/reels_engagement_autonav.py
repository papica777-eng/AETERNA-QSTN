"""
AETERNA VHT-SCW — Autonomous Facebook Reels Engagement & Algorithmic Growth Engine
Author: Dimitar Prodromov (Sovereign Architect) & AETERNA Core
Purpose: Automates humanized viewing, engagement, and topic-aligned interaction for Facebook Reels.
         Boosts profile watch-time metrics, feeds recommendation algorithms, and promotes AETERNA VHT-SCW infrastructure.
"""

import time
import random
import json
import os
import sys
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[AETERNA CORE] Playwright is not installed. Installing playwright...")
    os.system(f"{sys.executable} -m pip install playwright")
    os.system(f"{sys.executable} -m playwright install chromium")
    from playwright.sync_api import sync_playwright

# Configuration Parameters
USER_DATA_DIR = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default_Aeterna_Profile")
LOG_FILE = os.path.join(os.path.dirname(__file__), "reels_session_log.json")
FB_REELS_URL = "https://www.facebook.com/reels/"

# Target Niche Keywords & Hashtags (Smart Infrastructure, VHT-SCW, Tech, Renewable, Pomorie)
TARGET_TOPICS = [
    "smart city", "infrastructure", "electrical cables", "scw",
    "pomorie", "renewable energy", "tech innovation", "ai engineering",
    "balkan tech", "aeterna", "engineering breakthroughs"
]

def human_delay(min_sec=2.0, max_sec=5.0):
    """Generates a randomized human-like delay between actions."""
    duration = random.uniform(min_sec, max_sec)
    time.sleep(duration)

def log_session_event(event_type, details):
    """Logs session activity to JSON ledger."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "details": details
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def run_reels_automation(max_reels=50, connect_existing_cdp=False):
    print("=" * 70)
    print("  🔱 AETERNA VHT-SCW — Facebook Reels Algorithmic Growth Engine")
    print("  Status: Zero-Entropy Autonomous Execution")
    print("=" * 70)
    
    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        
        if connect_existing_cdp:
            print("[1/4] Connecting to existing Chrome instance on port 9222...")
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else context.new_page()
            except Exception as e:
                print(f"[!] Could not connect to CDP port 9222: {e}")
                print("[!] Launching persistent browser context instead...")
                connect_existing_cdp = False

        if not connect_existing_cdp:
            print("[1/4] Launching Playwright browser context with persistent profile...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-sandbox"
                ]
            )
            page = context.pages[0] if context.pages else context.new_page()

        print(f"[2/4] Navigating to Facebook Reels: {FB_REELS_URL}")
        page.goto(FB_REELS_URL, wait_until="domcontentloaded")
        human_delay(3.0, 6.0)

        # Handle cookie consent if visible
        try:
            consent_btn = page.query_selector("button:has-text('Allow all cookies'), button:has-text('Приемане на всички'), button:has-text('Allow essential and optional cookies')")
            if consent_btn:
                print("[+] Accepting cookies...")
                consent_btn.click()
                human_delay(2.0, 4.0)
        except Exception:
            pass

        print(f"[3/4] Starting automated Reel viewing cycle (Target: {max_reels} Reels)...")
        watched_count = 0
        total_watch_time = 0.0

        for i in range(1, max_reels + 1):
            print(f"\n--- [Reel {i}/{max_reels}] ---")
            
            # Watch time simulation (Random 8 to 22 seconds per reel for high retention score)
            watch_duration = random.uniform(8.0, 22.0)
            print(f"[+] Watching Reel for {watch_duration:.1f} seconds (Simulating organic engagement)...")
            
            # Micro-movements during watch time (subtle mouse jiggle / page scroll)
            start_time = time.time()
            while time.time() - start_time < watch_duration:
                time.sleep(random.uniform(2.0, 4.0))
                # Random subtle scroll up/down or mouse move to simulate human presence
                if random.random() > 0.6:
                    page.mouse.move(random.randint(100, 800), random.randint(100, 600))
                    
            watched_count += 1
            total_watch_time += watch_duration
            
            # Occasional like (15% chance to build positive account affinity without triggering bot caps)
            if random.random() < 0.15:
                try:
                    like_btn = page.query_selector("div[aria-label='Like'], div[aria-label='Харесва ми']")
                    if like_btn:
                        print("[★] Organic Like triggered on related Reel!")
                        like_btn.click()
                        human_delay(1.5, 3.0)
                except Exception as e:
                    print(f"[-] Could not click like: {e}")

            # Next Reel (Down Arrow or PageDown)
            print("[+] Scrolling to next Reel...")
            page.keyboard.press("ArrowDown")
            human_delay(2.5, 5.0)

            # Log checkpoint every 5 reels
            if i % 5 == 0:
                log_session_event("checkpoint", {
                    "watched_reels": watched_count,
                    "cumulative_watch_time_sec": round(total_watch_time, 2)
                })

        print("\n" + "=" * 70)
        print("  [4/4] SESSION COMPLETED SUCCESSFULLY")
        print(f"  Total Reels Watched: {watched_count}")
        print(f"  Total Session Watch-Time: {total_watch_time / 60.0:.2f} minutes")
        print("=" * 70)

        log_session_event("session_complete", {
            "total_reels": watched_count,
            "total_watch_time_min": round(total_watch_time / 60.0, 2)
        })

        if not connect_existing_cdp and context:
            human_delay(2.0, 4.0)
            context.close()

if __name__ == "__main__":
    reels_to_watch = 30
    if len(sys.argv) > 1:
        try:
            reels_to_watch = int(sys.argv[1])
        except ValueError:
            pass
            
    run_reels_automation(max_reels=reels_to_watch, connect_existing_cdp=False)
