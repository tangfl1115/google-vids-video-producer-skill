# -*- coding: utf-8 -*-
"""
Windows 非 C 槽工作區 vids-studio Native Host 權限與路徑白名單修補腳本
Version: 1.0.0
Changelog:
  - v1.0.0: 自動修補 Shugar86/vids-studio 之 native/platform_support.py，允許 D:\2026antigravity 路徑並將 Windows BUILTIN\Users (S-1-5-32-545) 與 Authenticated Users (S-1-5-11) SID 加入白名單。
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    bridge_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"d:\2026antigravity\.agents\tools\vids-studio")
    target = bridge_dir / "native" / "platform_support.py"
    if not target.exists():
        print(f"❌ 找不到 {target}")
        sys.exit(1)

    txt = target.read_text(encoding="utf-8")
    modified = False

    # 1. 放寬非 C:\Users 路徑限制
    old_path_check = 'if not _is_within(resolved, Path.home().resolve()):'
    new_path_check = 'if not (_is_within(resolved, Path.home().resolve()) or "2026antigravity" in str(resolved).lower()):'
    if old_path_check in txt:
        txt = txt.replace(old_path_check, new_path_check)
        modified = True

    # 2. 放寬 Windows BUILTIN\Users 與 Authenticated Users SID 檢查
    old_sid = '"S-1-5-32-544",  # Builtin Administrators'
    new_sid = '"S-1-5-32-544",  # Builtin Administrators\n        "S-1-5-32-545",  # Builtin Users\n        "S-1-5-11",      # Authenticated Users'
    if old_sid in txt and '"S-1-5-32-545"' not in txt:
        txt = txt.replace(old_sid, new_sid)
        modified = True

    if modified:
        target.write_text(txt, encoding="utf-8")
        print(f"✅ 已成功修補 Windows ACL 與路徑白名單：{target}")
    else:
        print(f"ℹ️ {target} 已包含修補內容，無須重複修改。")


if __name__ == "__main__":
    main()
