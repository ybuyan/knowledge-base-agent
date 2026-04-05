"""
清理 Skill 缓存
用于删除 skill 后清理内存中的缓存
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.skills.engine import SkillEngine


def main():
    print("=" * 60)
    print("清理 Skill 缓存")
    print("=" * 60)
    
    engine = SkillEngine()
    
    # 显示当前缓存的 skills
    print("\n当前缓存的 skills:")
    for skill_id, skill_def in engine.skill_loader._cache.items():
        skill_type = skill_def.frontmatter.get("skill_type", "qa")
        print(f"  - {skill_id} ({skill_type}): {skill_def.name}")
    
    # 重新加载所有 skills
    print("\n正在重新加载所有 skills...")
    engine.reload()
    
    # 显示重新加载后的 skills
    print("\n重新加载后的 skills:")
    for skill_id, skill_def in engine.skill_loader._cache.items():
        skill_type = skill_def.frontmatter.get("skill_type", "qa")
        print(f"  - {skill_id} ({skill_type}): {skill_def.name}")
    
    # 检查是否还有 leave_apply
    if "leave_apply" in engine.skill_loader._cache:
        print("\n❌ 警告：leave_apply 仍在缓存中！")
        print("   这不应该发生，请检查文件是否真的删除了。")
    else:
        print("\n✅ leave_apply 已从缓存中移除")
    
    # 检查 leave_guide 是否存在
    if "leave_guide" in engine.skill_loader._cache:
        leave_guide = engine.skill_loader._cache["leave_guide"]
        skill_type = leave_guide.frontmatter.get("skill_type", "qa")
        print(f"✅ leave_guide 已加载 (skill_type: {skill_type})")
    else:
        print("❌ 警告：leave_guide 未找到！")
    
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print("\n注意：如果后端服务正在运行，需要重启服务才能生效。")
    print("或者调用 API: POST /api/flow-config/skills/leave_apply/reload")


if __name__ == "__main__":
    main()
