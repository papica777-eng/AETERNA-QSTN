"""
AETERNA VHT World-Class 20-Second Reel Renderer (Playwright HTML5 + Pro Cyber Audio)
Author: Dimitar Prodromov (Sovereign Architect) & AETERNA Core
Renders a 20-second broadcast-grade video with exact Bulgarian messaging & live scrolling evidence background.
Output Destination: C:\\Users\\papic\\Desktop\\AETERNA_VHT_WORLDCLASS_20S_REEL.mp4
"""

import os
import sys
import math
import numpy as np
from PIL import Image
import moviepy as mp
from playwright.sync_api import sync_playwright

# Output Paths
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
OUTPUT_MP4 = os.path.join(DESKTOP_DIR, "AETERNA_VHT_WORLDCLASS_20S_REEL.mp4")
PREVIEW_PNG = os.path.join(DESKTOP_DIR, "AETERNA_VHT_WORLDCLASS_20S_PREVIEW.png")

HTML_TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "reel_template.html"))
HTML_URI = "file:///" + HTML_TEMPLATE_PATH.replace("\\", "/")

# Specs (20 Seconds at 30 FPS = 600 Frames)
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SEC = 20
TOTAL_FRAMES = FPS * DURATION_SEC

def generate_cinematic_audio(duration_sec=20.0, sample_rate=44100):
    """Synthesizes a 20-second cinematic cyber-pulse audio track with impact stingers."""
    total_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, False)
    
    # 1. Sub-bass synth drone (50Hz + 2Hz heartbeat pulse)
    sub_bass = np.sin(2 * np.pi * 50 * t) * 0.35
    heartbeat = (np.sin(2 * np.pi * 2.0 * t) ** 4) * 0.25
    
    # 2. Sovereign 432Hz harmonic wave
    freq_sweep = 432 + 40 * np.sin(2 * np.pi * 0.1 * t)
    harmonic = np.sin(2 * np.pi * freq_sweep * t) * 0.15
    
    # 3. Transition Stingers (at t = 0.0s, 5.0s, 10.0s, 15.0s)
    stingers = np.zeros_like(t)
    for stinger_time in [0.0, 5.0, 10.0, 15.0]:
        stinger_idx = int(stinger_time * sample_rate)
        decay_samples = int(0.7 * sample_rate)
        if stinger_idx < total_samples:
            end_idx = min(total_samples, stinger_idx + decay_samples)
            stinger_t = np.linspace(0, 0.7, end_idx - stinger_idx, False)
            decay = np.exp(-5.5 * stinger_t)
            impact = (np.sin(2 * np.pi * 75 * stinger_t) + np.sin(2 * np.pi * 150 * stinger_t)) * decay * 0.55
            stingers[stinger_idx:end_idx] += impact
            
    master_wave = sub_bass + heartbeat + harmonic + stingers
    max_val = np.max(np.abs(master_wave))
    if max_val > 0:
        master_wave = (master_wave / max_val) * 0.85
        
    stereo = np.vstack([master_wave, master_wave]).T
    return mp.AudioArrayClip(stereo, fps=sample_rate)

def main():
    print("=" * 75)
    print("  🔱 AETERNA VHT — World-Class 20s Reel Renderer (Playwright HTML5)")
    print(f"  Target Video Output: {OUTPUT_MP4}")
    print(f"  HTML URI: {HTML_URI}")
    print("=" * 75)

    print("[1/4] Synthesizing 20-second 44.1kHz Pro Cyber Audio Track...")
    audio_clip = generate_cinematic_audio(DURATION_SEC, 44100)

    print("[2/4] Rendering 600 frames via Playwright Chromium Engine...")
    frames_numpy = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.goto(HTML_URI, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)  # Allow Google Fonts to render

        for i in range(TOTAL_FRAMES):
            t_sec = i / FPS
            if i % 60 == 0:
                print(f"      Rendering Frame {i}/{TOTAL_FRAMES} (t = {t_sec:.1f}s)...")
                
            page.evaluate(f"window.setSceneTime({t_sec:.3f})")
            screenshot_bytes = page.screenshot(type="png", omit_background=True)
            
            import io
            img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
            frames_numpy.append(np.array(img))

        browser.close()

    print("[3/4] Multiplexing Playwright Video Frames with Pro Cyber Audio Track...")
    video_clip = mp.ImageSequenceClip(frames_numpy, fps=FPS)
    final_clip = video_clip.with_audio(audio_clip)

    final_clip.write_videofile(
        OUTPUT_MP4,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="14000k",
        logger="bar"
    )

    print("[4/4] Generating World-Class Preview Keyframe Grid PNG...")
    f1 = Image.fromarray(frames_numpy[75])   # Scene 1 (2.5s)
    f2 = Image.fromarray(frames_numpy[225])  # Scene 2 (7.5s)
    f3 = Image.fromarray(frames_numpy[375])  # Scene 3 (12.5s)
    f4 = Image.fromarray(frames_numpy[525])  # Scene 4 (17.5s)

    w_half, h_half = 540, 960
    grid = Image.new('RGB', (1080, 1920), (3, 7, 18))
    grid.paste(f1.resize((w_half, h_half)), (0, 0))
    grid.paste(f2.resize((w_half, h_half)), (540, 0))
    grid.paste(f3.resize((w_half, h_half)), (0, 960))
    grid.paste(f4.resize((w_half, h_half)), (540, 960))

    from PIL import ImageDraw
    grid_draw = ImageDraw.Draw(grid)
    grid_draw.line([(540, 0), (540, 1920)], fill=(6, 182, 212), width=4)
    grid_draw.line([(0, 960), (1080, 960)], fill=(6, 182, 212), width=4)
    grid.save(PREVIEW_PNG)

    print("\n" + "=" * 75)
    print("  ★ WORLD-CLASS 20S REEL VIDEO & AUDIO READY ON DESKTOP:")
    print(f"  🎬 Video File: {OUTPUT_MP4}")
    print(f"  🖼️ Preview Image: {PREVIEW_PNG}")
    print("=" * 75)

if __name__ == "__main__":
    main()
