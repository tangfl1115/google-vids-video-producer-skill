# -*- coding: utf-8 -*-
"""
Google Vids 1080p 成片雙色繁中硬字幕燒錄與四大分類自動歸檔引擎
Version: 3.1.0
Changelog:
  - v3.1.0: 解決 Google Vids 原生語音具大陸捲舌音問題！內建 100% 道地台灣國語（Microsoft edge-tts `zh-TW-YunJheNeural` 雲哲 / `zh-TW-HsiaoChenNeural` 曉臻）合成引擎，自動按 10.0 秒分鏡毫秒級對齊混音，徹底消除大陸捲舌音，產出純淨無字幕母帶與繁中雙色硬字幕正式版，並自動歸檔至『Google Vids 影片』四大分類。
  - v3.0.0: 依實測 Omni 10.0 秒單鏡時長自動生成雙色 ASS 字幕檔、備份純淨無字幕母帶、壓制 H.264 1080p 硬字幕正式版，並依四大頻道分類（［手作科學］、［國小自然］、［大識界 開眼界］、［AI 自學筆記］）自動歸檔至『Google Vids 影片』資料夾。
"""

import sys
import json
import shutil
import asyncio
import argparse
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import edge_tts
except ImportError:
    edge_tts = None

VALID_CATEGORIES = [
    "［手作科學］",
    "［國小自然］",
    "［大識界 開眼界］",
    "［AI 自學筆記］",
]

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft JhengHei,58,&H00FFFFFF,&H0000FFFF,&H001A1A1A,&H80000000,-1,0,0,0,100,100,2,0,1,4,2,2,60,60,55,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def fmt_ass_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(manifest: dict, out_ass: Path, clip_dur: float = 10.0):
    lines = [ASS_HEADER.strip(), ""]
    for idx, sc in enumerate(manifest.get("scenes", [])):
        base = idx * clip_dur
        subs = sc.get("subtitles") or []
        if len(subs) == 2:
            lines.append(f"Dialogue: 0,{fmt_ass_time(base + 0.30)},{fmt_ass_time(base + 4.80)},Default,,0,0,0,,{subs[0]}")
            lines.append(f"Dialogue: 0,{fmt_ass_time(base + 4.90)},{fmt_ass_time(base + clip_dur - 0.35)},Default,,0,0,0,,{subs[1]}")
        elif len(subs) == 1:
            lines.append(f"Dialogue: 0,{fmt_ass_time(base + 0.30)},{fmt_ass_time(base + clip_dur - 0.35)},Default,,0,0,0,,{subs[0]}")
        elif sc.get("narration_zh"):
            lines.append(f"Dialogue: 0,{fmt_ass_time(base + 0.30)},{fmt_ass_time(base + clip_dur - 0.35)},Default,,0,0,0,,{sc['narration_zh']}")
    out_ass.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def synthesize_tw_scene_audio(text: str, voice: str, out_path: Path):
    if not edge_tts:
        raise RuntimeError("未安裝 edge-tts，請執行 pip install edge-tts")
    comm = edge_tts.Communicate(text, voice=voice, rate="+0%")
    await comm.save(str(out_path))


def generate_taiwan_master_voice(manifest: dict, proj_dir: Path, voice: str = "zh-TW-YunJheNeural", clip_dur: float = 10.0) -> Path:
    """自動為每一鏡合成 100% 台灣國語音軌並毫秒級對齊時間軸"""
    audio_dir = proj_dir / "audio_tracks"
    audio_dir.mkdir(parents=True, exist_ok=True)
    scenes = manifest.get("scenes", [])

    inputs = []
    filter_parts = []

    for i, sc in enumerate(scenes):
        sc_id = sc.get("id", f"S{i+1:02d}")
        # 取得台詞文本
        narration = sc.get("narration_zh") or ""
        if not narration and sc.get("subtitles"):
            # 將雙色標籤去除取得純文字
            narration = "".join(sc["subtitles"])
            import re
            narration = re.sub(r"\{\\.*?\}", "", narration)
        if not narration and sc.get("prompt"):
            import re
            m = re.search(r"「(.*?)」", sc["prompt"])
            if m:
                narration = m.group(1)

        out_mp3 = audio_dir / f"{sc_id}_tw.mp3"
        if not out_mp3.exists() or out_mp3.stat().st_size < 1000:
            print(f"  🎙️ 正在合成 {sc_id} 台灣國語旁白 ({voice}): 「{narration[:25]}...」")
            asyncio.run(synthesize_tw_scene_audio(narration, voice, out_mp3))

        delay_ms = int((i * clip_dur + 0.6) * 1000)
        inputs.extend(["-i", str(out_mp3)])
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(scenes)))
    filter_complex = f"{';'.join(filter_parts)};{mix_inputs}amix=inputs={len(scenes)}:duration=longest:normalize=0[aout]"

    out_voice = proj_dir / "voice_taiwanese_full.wav"
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, "-map", "[aout]", "-c:a", "pcm_s16le", str(out_voice)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"合成台灣國語主音軌失敗：\n{p.stderr[-500:]}")
    print(f"✅ 已完成全片 100% 台灣國語無捲舌音軌合成：{out_voice.name}")
    return out_voice


def main():
    parser = argparse.ArgumentParser(description="Google Vids 1080p 硬字幕燒錄與分類歸檔")
    parser.add_argument("--manifest", required=True, help="vids_project_manifest.json 路徑")
    parser.add_argument("--mp4", required=False, help="下載的原始 MP4 路徑")
    parser.add_argument("--voice", default="zh-TW-YunJheNeural", help="台灣國語語音 (zh-TW-YunJheNeural 男聲 或 zh-TW-HsiaoChenNeural 女聲)")
    parser.add_argument("--archive-root", default=r"d:\2026antigravity\Google Vids 影片", help="Google Vids 影片分類總目錄")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    proj_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    title = manifest.get("project_title", proj_dir.name)
    category = manifest.get("youtube_category", "［手作科學］")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"youtube_category 必須為四大固定分類之一：{VALID_CATEGORIES}")

    subbed_mp4 = proj_dir / f"{title}.mp4"
    clean_mp4 = proj_dir / f"{title}_純淨無字幕版.mp4"

    src_mp4 = Path(args.mp4).resolve() if args.mp4 else (subbed_mp4 if subbed_mp4.exists() else clean_mp4)
    if not src_mp4.exists():
        raise FileNotFoundError(f"找不到輸入 MP4：{src_mp4}")

    # 1. 自動合成 100% 台灣國語主音軌（無大陸捲舌音）
    tw_voice_wav = generate_taiwan_master_voice(manifest, proj_dir, voice=args.voice, clip_dur=10.0)

    # 2. 備份/替換純淨無字幕母帶 (1080p + 台灣國語音軌)
    temp_clean = proj_dir / "temp_clean.mp4"
    cmd_clean = [
        "ffmpeg", "-y",
        "-i", str(src_mp4),
        "-i", str(tw_voice_wav),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        str(temp_clean)
    ]
    p_clean = subprocess.run(cmd_clean, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p_clean.returncode != 0:
        raise RuntimeError(f"替換台灣國語母帶失敗：\n{p_clean.stderr[-500:]}")
    shutil.move(str(temp_clean), str(clean_mp4))
    print(f"✅ 已完成純淨無字幕母帶 (100% 台灣國語)：{clean_mp4.name}")

    # 3. 壓制繁體中文雙色硬字幕正式版
    ass_path = proj_dir / "subtitles.ass"
    if not ass_path.exists():
        build_ass(manifest, ass_path, clip_dur=10.0)
        print(f"✅ 已產生 10.0 秒每鏡對齊之雙色字幕檔：{ass_path.name}")

    temp_subbed = proj_dir / "temp_subbed.mp4"
    cmd_sub = [
        "ffmpeg", "-y",
        "-i", clean_mp4.name,
        "-vf", "ass=subtitles.ass",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        str(temp_subbed),
    ]
    p_sub = subprocess.run(cmd_sub, cwd=str(proj_dir), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p_sub.returncode != 0:
        raise RuntimeError(f"FFmpeg 字幕壓制失敗：\n{p_sub.stderr[-600:]}")
    shutil.move(str(temp_subbed), str(subbed_mp4))
    print(f"✅ 已完成 1080p 內嵌繁中雙色硬字幕正式版 (100% 台灣國語)：{subbed_mp4.name}")

    # 4. 自動歸檔至 Google Vids 影片\<類別>\<專案名稱>\
    archive_root = Path(args.archive_root)
    for c in VALID_CATEGORIES:
        (archive_root / c).mkdir(parents=True, exist_ok=True)

    target_dir = archive_root / category / title
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in [subbed_mp4, clean_mp4, ass_path, tw_voice_wav, manifest_path, proj_dir / f"YouTube發布資訊_{title}.txt"]:
        if f.exists():
            shutil.copy2(f, target_dir / f.name)

    print(f"📂 已自動依類別【{category}】歸檔至：{target_dir}")


if __name__ == "__main__":
    main()
