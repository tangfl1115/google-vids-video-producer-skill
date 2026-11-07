# -*- coding: utf-8 -*-
"""
Google Vids 1080p 成片雙色繁中硬字幕燒錄與四大分類自動歸檔引擎
Version: 3.0.0
Changelog:
  - v3.0.0: 依實測 Omni 10.0 秒單鏡時長自動生成雙色 ASS 字幕檔、備份純淨無字幕母帶、壓制 H.264 1080p 硬字幕正式版，並依四大頻道分類（［手作科學］、［國小自然］、［大識界 開眼界］、［AI 自學筆記］）自動歸檔至『Google Vids 影片』資料夾。
"""

import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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


def main():
    parser = argparse.ArgumentParser(description="Google Vids 1080p 硬字幕燒錄與分類歸檔")
    parser.add_argument("--manifest", required=True, help="vids_project_manifest.json 路徑")
    parser.add_argument("--mp4", required=False, help="下載的原始 MP4 路徑")
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

    src_mp4 = Path(args.mp4).resolve() if args.mp4 else subbed_mp4
    if not src_mp4.exists():
        raise FileNotFoundError(f"找不到輸入 MP4：{src_mp4}")

    if not clean_mp4.exists():
        shutil.copy2(src_mp4, clean_mp4)
        print(f"✅ 已備份純淨無字幕母帶：{clean_mp4.name}")

    ass_path = proj_dir / "subtitles.ass"
    if not ass_path.exists():
        build_ass(manifest, ass_path, clip_dur=10.0)
        print(f"✅ 已產生 10.0 秒每鏡對齊之雙色字幕檔：{ass_path.name}")

    cmd = [
        "ffmpeg", "-y",
        "-i", clean_mp4.name,
        "-vf", "ass=subtitles.ass",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        subbed_mp4.name,
    ]
    p = subprocess.run(cmd, cwd=str(proj_dir), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"FFmpeg 字幕壓制失敗：\n{p.stderr[-600:]}")
    print(f"✅ 已完成 1080p 內嵌繁中雙色硬字幕正式版：{subbed_mp4}")

    # 自動歸檔至 Google Vids 影片\<類別>\<專案名稱>\
    archive_root = Path(args.archive_root)
    for c in VALID_CATEGORIES:
        (archive_root / c).mkdir(parents=True, exist_ok=True)

    target_dir = archive_root / category / title
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in [subbed_mp4, clean_mp4, ass_path, manifest_path, proj_dir / f"YouTube發布資訊_{title}.txt"]:
        if f.exists():
            shutil.copy2(f, target_dir / f.name)

    print(f"📂 已自動依類別【{category}】歸檔至：{target_dir}")


if __name__ == "__main__":
    main()
