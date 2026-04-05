#!/usr/bin/env python
"""删除 uploads 目录中的所有文件"""
import os
import glob
import time

def delete_uploads():
    upload_dir = "data/uploads"
    files = glob.glob(f"{upload_dir}/*")
    deleted = 0
    errors = []
    
    for f in files:
        # 跳过临时文件
        if os.path.basename(f).startswith("~"):
            continue
        try:
            os.remove(f)
            deleted += 1
            print(f"已删除: {f}")
        except PermissionError:
            errors.append(f"被占用: {f}")
        except Exception as e:
            errors.append(f"{f}: {e}")
    
    print(f"\n删除完成: {deleted} 个文件")
    if errors:
        print(f"失败: {len(errors)} 个文件")
        for e in errors:
            print(f"  - {e}")

if __name__ == "__main__":
    delete_uploads()
