"""
强制重新加载所有 skills 并验证
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 重要：清除模块缓存
if 'app.skills.engine' in sys.modules:
    del sys.modules['app.skills.engine']
if 'app.skills.skill_loader' in sys.modules:
    del sys.modules['app.skills.skill_loader']

from app.skills.engine import SkillEngine


def main():
    print("=" * 70)
    print("强制重新加载 Skills")
    print("=" * 70)
    
    # 重置单例
    SkillEngine._instance = None
    SkillEngine._initialized = False
    
    # 创建新实例
    engine = SkillEngine()
    
    print("\n当前加载的 skills:")
    print("-" * 70)
    
    for skill_id, skill_def in engine.skill_loader._cache.items():
        skill_type = skill_def.frontmatter.get("skill_type", "qa")
        triggers = skill_def.frontmatter.get("triggers", [])
        
        print(f"\n📦 {skill_id}")
        print(f"   名称: {skill_def.name}")
        print(f"   类型: {skill_type}")
        print(f"   描述: {skill_def.description}")
        if triggers:
            print(f"   触发词: {', '.join(triggers[:3])}")
    
    print("\n" + "=" * 70)
    
    # 检查 leave 相关的 skills
    leave_skills = [
        sid for sid in engine.skill_loader._cache.keys()
        if 'leave' in sid.lower() or '请假' in engine.skill_loader._cache[sid].name
    ]
    
    if leave_skills:
        print(f"\n⚠️  发现 {len(leave_skills)} 个请假相关的 skills:")
        for sid in leave_skills:
            skill = engine.skill_loader._cache[sid]
            skill_type = skill.frontmatter.get("skill_type", "qa")
            print(f"   - {sid} (类型: {skill_type})")
    else:
        print("\n✅ 没有发现请假相关的 skills")
    
    # 检查 process 类型的 skills
    process_skills = [
        sid for sid, skill in engine.skill_loader._cache.items()
        if skill.frontmatter.get("skill_type") == "process"
    ]
    
    print(f"\n📋 Process 类型的 skills ({len(process_skills)} 个):")
    if process_skills:
        for sid in process_skills:
            skill = engine.skill_loader._cache[sid]
            print(f"   - {sid}: {skill.name}")
    else:
        print("   (无)")
    
    print("\n" + "=" * 70)
    print("提示：如果后端服务正在运行，请重启服务以应用更改")
    print("=" * 70)


if __name__ == "__main__":
    main()
