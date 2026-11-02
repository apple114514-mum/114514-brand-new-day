#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人才发展计划 质量检查脚本
"""

import sys
from pathlib import Path


def check_skill_quality(skill_path: str) -> bool:
    """检查技能包质量"""
    skill_dir = Path(skill_path)
    
    # 检查必要文件是否存在
    required_files = [
        "SKILL.md",
        "manifest.yaml",
        "references/theory.md",
        "references/examples.md",
        "scripts/__init__.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not (skill_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺失文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 质量检查通过")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python quality_check.py <skill_path>")
        sys.exit(1)
    
    skill_path = sys.argv[1]
    success = check_skill_quality(skill_path)
    sys.exit(0 if success else 1)
