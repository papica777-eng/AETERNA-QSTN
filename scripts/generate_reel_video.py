"""
AETERNA VHT-SCW & ONCOLOGY — Pro Broadcast Cinematic Facebook Reel Video (1080x1920, 9:16)
Author: Dimitar Prodromov (Sovereign Architect) & AETERNA Core
Renders a broadcast-grade 15-second vertical video file with synthesized cinematic cyber audio.
Export Destination: C:\\Users\\papic\\Desktop\\AETERNA_VHT_REEL_PROMO_PRO.mp4
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import moviepy as mp

# Output Path
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
OUTPUT_MP4 = os.path.join(DESKTOP_DIR, "AETERNA_VHT_REEL_PROMO_PRO.mp4")
PREVIEW_PNG = os.path.join(DESKTOP_DIR, "AETERNA_VHT_REEL_PREVIEW_PRO.png")

# Video Specifications
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SEC = 15
TOTAL_FRAMES = FPS * DURATION_SEC

# Palette
COLOR_BG_DARK = (5, 7, 12)
COLOR_CYAN = (6, 182, 212)
COLOR_PURPLE = (139, 92, 246)
COLOR_EMERALD = (16, 185, 129)
COLOR_GOLD = (245, 158, 11)
COLOR_RED = (239, 68, 68)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (148, 163, 184)
COLOR_CARD_BG = (15, 23, 42)

# Load Fonts
def get_font(size, bold=False):
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "Segoe UI Bold.ttf" if bold else "Segoe UI.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()

FONT_HEADER = get_font(54, bold=True)
FONT_SUBHEADER = get_font(36, bold=True)
FONT_BODY = get_font(28, bold=False)
FONT_BADGE = get_font(24, bold=True)
FONT_BIG_NUM = get_font(68, bold=True)

def draw_rounded_rectangle(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def generate_cinematic_audio(duration_sec=15.0, sample_rate=44100):
    """Synthesizes a 15-second cinematic cyber-pulse audio track with impact stingers."""
    total_samples = int(sample_rate * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, False)
    
    # 1. Sub-bass pulse (50Hz synth drone with 2Hz heartbeat pulse)
    sub_bass = np.sin(2 * np.pi * 50 * t) * 0.35
    heartbeat = (np.sin(2 * np.pi * 2.0 * t) ** 4) * 0.25
    
    # 2. Rising 432Hz harmonic wave (Sovereign 432Hz Global Resonance)
    freq_sweep = 432 + 50 * np.sin(2 * np.pi * 0.1 * t)
    harmonic = np.sin(2 * np.pi * freq_sweep * t) * 0.15
    
    # 3. Transition Impact Stingers (at t = 0.0s, 3.8s, 7.8s, 11.8s)
    stingers = np.zeros_like(t)
    for stinger_time in [0.0, 3.8, 7.8, 11.8]:
        stinger_idx = int(stinger_time * sample_rate)
        decay_samples = int(0.6 * sample_rate)
        if stinger_idx < total_samples:
            end_idx = min(total_samples, stinger_idx + decay_samples)
            stinger_t = np.linspace(0, 0.6, end_idx - stinger_idx, False)
            decay = np.exp(-6.0 * stinger_t)
            impact = (np.sin(2 * np.pi * 80 * stinger_t) + np.sin(2 * np.pi * 160 * stinger_t)) * decay * 0.5
            stingers[stinger_idx:end_idx] += impact
            
    # Combine & master audio channel
    master_wave = sub_bass + heartbeat + harmonic + stingers
    # Normalize to avoid clipping
    max_val = np.max(np.abs(master_wave))
    if max_val > 0:
        master_wave = (master_wave / max_val) * 0.85
        
    stereo = np.vstack([master_wave, master_wave]).T
    return mp.AudioArrayClip(stereo, fps=sample_rate)

def render_frame(frame_idx):
    t = frame_idx / FPS
    progress = frame_idx / TOTAL_FRAMES
    
    # Base Canvas
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # Background Gridlines
    grid_spacing = 70
    grid_offset = int((t * 35) % grid_spacing)
    for y in range(-grid_spacing, HEIGHT + grid_spacing, grid_spacing):
        draw.line([(0, y + grid_offset), (WIDTH, y + grid_offset)], fill=(15, 23, 40), width=1)
    for x in range(0, WIDTH, grid_spacing):
        draw.line([(x, 0), (x, HEIGHT)], fill=(15, 23, 40), width=1)
        
    # Animated Radar Scan Line
    scan_y = int((t * 350) % HEIGHT)
    draw.line([(0, scan_y), (WIDTH, scan_y)], fill=(6, 182, 212), width=3)
    
    # Animated Audio Visualizer Spectrum Bar at bottom
    num_bars = 28
    bar_width = 24
    gap = 12
    start_x = (WIDTH - (num_bars * (bar_width + gap))) // 2
    for b in range(num_bars):
        h_val = int(30 + 80 * abs(math.sin(t * 8.0 + b * 0.4)))
        bx = start_x + b * (bar_width + gap)
        by = HEIGHT - 180 - h_val
        draw_rounded_rectangle(draw, [bx, by, bx + bar_width, HEIGHT - 180], radius=4, fill=COLOR_CYAN)

    # Header Badge (Pulsing Top Badge)
    badge_rect = [WIDTH // 2 - 270, 130, WIDTH // 2 + 270, 195]
    draw_rounded_rectangle(draw, badge_rect, radius=15, fill=(15, 23, 42), outline=COLOR_CYAN, width=2)
    draw.text((WIDTH // 2, 162), "🇧🇬 AETERNA // ИСТИНАТА ЗА БЪЛГАРСКАТА НАУКА", fill=COLOR_CYAN, font=FONT_BADGE, anchor="mm")

    if t < 3.8:
        # SCENE 1: THE TRUTH & PUBLIC REVOLUTION
        card_rect = [70, 420, WIDTH - 70, 1180]
        draw_rounded_rectangle(draw, card_rect, radius=26, fill=(15, 23, 42), outline=COLOR_RED, width=3)
        
        draw.text((WIDTH // 2, 490), "СВЕТОВЕН ПРОБИВ В", fill=COLOR_RED, font=FONT_HEADER, anchor="mm")
        draw.text((WIDTH // 2, 560), "БОРБАТА С РАКА И", fill=COLOR_WHITE, font=FONT_HEADER, anchor="mm")
        draw.text((WIDTH // 2, 630), "КИБЕРСИГУРНОСТТА!", fill=COLOR_CYAN, font=FONT_HEADER, anchor="mm")
        
        draw.line([(130, 690), (WIDTH - 130, 690)], fill=COLOR_RED, width=2)
        
        draw.text((WIDTH // 2, 765), "Докато държавата и институциите мълчат,", fill=COLOR_GRAY, font=FONT_BODY, anchor="mm")
        draw.text((WIDTH // 2, 810), "ние постигнахме доказани резултати!", fill=COLOR_WHITE, font=FONT_SUBHEADER, anchor="mm")
        
        # Pill
        pill_rect = [100, 910, WIDTH - 100, 1050]
        draw_rounded_rectangle(draw, pill_rect, radius=18, fill=(35, 20, 30), outline=COLOR_GOLD, width=2)
        draw.text((WIDTH // 2, 980), "🔥 РЕЗУЛТАТИТЕ СЕ НАЛАГАТ КАТО СТАНДАРТ!", fill=COLOR_GOLD, font=FONT_SUBHEADER, anchor="mm")

    elif t < 7.8:
        # SCENE 2: CANCER VHT & APOPTOSIS LYSIS
        card_rect = [70, 360, WIDTH - 70, 1380]
        draw_rounded_rectangle(draw, card_rect, radius=26, fill=(15, 23, 42), outline=COLOR_CYAN, width=3)
        
        draw.text((WIDTH // 2, 435), "ДИГИТАЛЕН БЛИЗНАК (VHT)", fill=COLOR_WHITE, font=FONT_SUBHEADER, anchor="mm")
        draw.text((WIDTH // 2, 490), "97.13% ТОЧНОСТ СРЕЩУ РАКА", fill=COLOR_CYAN, font=FONT_HEADER, anchor="mm")

        # Metric 1: Apoptosis Precision
        m1_rect = [110, 570, WIDTH - 110, 770]
        draw_rounded_rectangle(draw, m1_rect, radius=16, fill=(20, 30, 50), outline=COLOR_EMERALD, width=2)
        draw.text((150, 620), "97.13%", fill=COLOR_EMERALD, font=FONT_BIG_NUM)
        draw.text((430, 630), "C-Index Точност (EU Стандарт)", fill=COLOR_WHITE, font=FONT_SUBHEADER)
        draw.text((430, 680), "Счупи задължителния праг C >= 75%", fill=COLOR_GRAY, font=FONT_BODY)

        # Metric 2: 87 Genomic Drivers
        m2_rect = [110, 800, WIDTH - 110, 1000]
        draw_rounded_rectangle(draw, m2_rect, radius=16, fill=(20, 30, 50), outline=COLOR_PURPLE, width=2)
        draw.text((150, 850), "87 Гена", fill=COLOR_PURPLE, font=FONT_BIG_NUM)
        draw.text((430, 860), "ONCOPANEL_87 LOINC Масив", fill=COLOR_WHITE, font=FONT_SUBHEADER)
        draw.text((430, 910), "KRAS, TP53, EGFR, BRCA1 симулация", fill=COLOR_GRAY, font=FONT_BODY)

        # Metric 3: Survival Extension
        m3_rect = [110, 1030, WIDTH - 110, 1230]
        draw_rounded_rectangle(draw, m3_rect, radius=16, fill=(20, 30, 50), outline=COLOR_GOLD, width=2)
        draw.text((150, 1080), "+91.3%", fill=COLOR_GOLD, font=FONT_BIG_NUM)
        draw.text((430, 1090), "Удължаване на Преживяемостта", fill=COLOR_WHITE, font=FONT_SUBHEADER)
        draw.text((430, 1140), "Спрямо конвенционалната химиотерапия", fill=COLOR_GRAY, font=FONT_BODY)

    elif t < 11.8:
        # SCENE 3: UNDERWATER CYBERSECURITY & VHT-SCW
        card_rect = [70, 380, WIDTH - 70, 1340]
        draw_rounded_rectangle(draw, card_rect, radius=26, fill=(15, 23, 42), outline=COLOR_EMERALD, width=3)
        
        draw.text((WIDTH // 2, 450), "ПОДВОДНА КИБЕРСИГУРНОСТ", fill=COLOR_EMERALD, font=FONT_HEADER, anchor="mm")
        draw.text((WIDTH // 2, 520), "& СМАРТ ИНФРАСТРУКТУРА", fill=COLOR_WHITE, font=FONT_HEADER, anchor="mm")

        draw.line([(130, 580), (WIDTH - 130, 580)], fill=COLOR_EMERALD, width=2)

        bullets = [
            "🛡️ VHT-SCW: Защита на подводни кабели и мрежи",
            "⚡ 10 kW Монолит със 100kHz MPPT софтуер",
            "🇪🇺 Horizon Europe Проект ID: 101347293",
            "🚀 EIC Accelerator Научен масив: €17.35M",
            "🧪 78/78 Преминати теста (0.0000 Ентропия)"
        ]
        y_pos = 630
        for b in bullets:
            b_rect = [110, y_pos, WIDTH - 110, y_pos + 95]
            draw_rounded_rectangle(draw, b_rect, radius=14, fill=(20, 32, 50), outline=(40, 55, 85), width=1)
            draw.text((140, y_pos + 47), b, fill=COLOR_WHITE, font=FONT_BODY, anchor="lm")
            y_pos += 120

    else:
        # SCENE 4: CALL TO ACTION (CTA)
        card_rect = [70, 420, WIDTH - 70, 1280]
        draw_rounded_rectangle(draw, card_rect, radius=26, fill=(15, 23, 42), outline=COLOR_CYAN, width=3)

        draw.text((WIDTH // 2, 500), "НАРОДЪТ ЗАСЛУЖАВА ИСТИНАТА!", fill=COLOR_GOLD, font=FONT_HEADER, anchor="mm")
        draw.text((WIDTH // 2, 570), "ВЛЕЗ И ТЕСТВАЙ LIVE ДНЕС", fill=COLOR_WHITE, font=FONT_HEADER, anchor="mm")

        # Portal Box
        portal_rect = [110, 670, WIDTH - 110, 840]
        draw_rounded_rectangle(draw, portal_rect, radius=20, fill=(6, 182, 212), outline=COLOR_WHITE, width=3)
        draw.text((WIDTH // 2, 755), "🌐 aeterna.website", fill=(7, 9, 14), font=FONT_HEADER, anchor="mm")

        draw.text((WIDTH // 2, 920), "🩺 Doctor Clinical Portal & AI Copilot", fill=COLOR_CYAN, font=FONT_SUBHEADER, anchor="mm")
        draw.text((WIDTH // 2, 985), "⚡ 0.0000 Ентропия • НЯМА КОЙ ДА НИ СПРЕ!", fill=COLOR_EMERALD, font=FONT_SUBHEADER, anchor="mm")

    # Bottom Footer
    draw.line([(0, HEIGHT - 100), (WIDTH, HEIGHT - 100)], fill=(30, 40, 65), width=2)
    progress_w = int(WIDTH * progress)
    draw.line([(0, HEIGHT - 100), (progress_w, HEIGHT - 100)], fill=COLOR_CYAN, width=6)
    
    draw.text((WIDTH // 2, HEIGHT - 55), "AETERNA SOVEREIGN LABS // ARCHITECT: DIMITAR PRODROMOV", fill=COLOR_GRAY, font=FONT_BADGE, anchor="mm")

    return np.array(img)

def main():
    print("=" * 75)
    print("  🔱 AETERNA VHT — Render Pro Cinematic Facebook Reel with Audio")
    print(f"  Target Output Video: {OUTPUT_MP4}")
    print(f"  Specs: 1080x1920 (9:16) | 30 FPS | {DURATION_SEC} Seconds | Cyber Audio Track")
    print("=" * 75)

    print("[1/4] Synthesizing 15-second cinematic cyber audio track (44.1kHz)...")
    audio_clip = generate_cinematic_audio(DURATION_SEC, 44100)

    print("[2/4] Rendering 450 vertical video frames (1080x1920)...")
    frames = []
    for i in range(TOTAL_FRAMES):
        if i % 45 == 0:
            print(f"      Rendering Frame {i}/{TOTAL_FRAMES} ({i/FPS:.1f}s)...")
        frame = render_frame(i)
        frames.append(frame)

    print("[3/4] Multiplexing video and audio tracks via MoviePy...")
    video_clip = mp.ImageSequenceClip(frames, fps=FPS)
    final_clip = video_clip.with_audio(audio_clip)

    final_clip.write_videofile(
        OUTPUT_MP4,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="9000k",
        logger="bar"
    )

    print("[4/4] Generating Keyframe Preview Grid PNG...")
    f1 = Image.fromarray(render_frame(60))   # Scene 1
    f2 = Image.fromarray(render_frame(180))  # Scene 2
    f3 = Image.fromarray(render_frame(300))  # Scene 3
    f4 = Image.fromarray(render_frame(420))  # Scene 4

    w_half, h_half = 540, 960
    grid = Image.new('RGB', (1080, 1920), (5, 7, 12))
    grid.paste(f1.resize((w_half, h_half)), (0, 0))
    grid.paste(f2.resize((w_half, h_half)), (540, 0))
    grid.paste(f3.resize((w_half, h_half)), (0, 960))
    grid.paste(f4.resize((w_half, h_half)), (540, 960))

    grid_draw = ImageDraw.Draw(grid)
    grid_draw.line([(540, 0), (540, 1920)], fill=(6, 182, 212), width=4)
    grid_draw.line([(0, 960), (1080, 960)], fill=(6, 182, 212), width=4)
    grid.save(PREVIEW_PNG)

    print("\n" + "=" * 75)
    print("  ★ PRO BROADCAST REEL VIDEO & AUDIO READY ON DESKTOP:")
    print(f"  🎬 Video File: {OUTPUT_MP4}")
    print(f"  🖼️ Preview Image: {PREVIEW_PNG}")
    print("=" * 75)

if __name__ == "__main__":
    main()
