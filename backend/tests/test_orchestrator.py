"""
测试 Orchestrator 的意图识别
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.skills.engine import SkillEngine


def test_get_process_skills():
    """测试获取 process 类型的 skills"""
    print("=" * 70)
    print("测试 _get_process_skills() 函数")
    print("=" * 70)
    
    # 模拟 orchestrator 中的 _get_process_skills() 函数
    try:
        engine = SkillEngine()
        process_skills = [
            {"id": s["id"], "description": s["description"]}
            for s in engine.list_skills()
            if engine.skill_loader._cache.get(s["id"]) and
               engine.skill_loader._cache[s["id"]].frontmatter.get("skill_type") == "process"
        ]
        
        print(f"\n找到 {len(process_skills)} 个 process 类型的 skills:\n")
        
        if process_skills:
            for skill in process_skills:
                print(f"  - {skill['id']}: {skill['description']}")
        else:
            print("  (无)")
        
        # 检查是否有 leave 相关的
        leave_related = [s for s in process_skills if 'leave' in s['id'].lower() or '请假' in s['description']]
        
        if leave_related:
            print(f"\n⚠️  警告：发现 {len(leave_related)} 个请假相关的 process skills:")
            for skill in leave_related:
                print(f"  - {skill['id']}: {skill['description']}")
            print("\n这就是为什么系统还在提示「您是想发起请假吗？」")
            print("解决方案：重启后端服务")
        else:
            print("\n✅ 没有请假相关的 process skills")
            print("如果前端仍然显示旧行为，说明后端服务没有重启")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 70)


def test_all_skills():
    """显示所有 skills 的类型"""
    print("\n所有 skills 的详细信息:")
    print("=" * 70)
    
    engine = SkillEngine()
    
    for skill_id, skill_def in engine.skill_loader._cache.items():
        skill_type = skill_def.frontmatter.get("skill_type", "qa")
        triggers = skill_def.frontmatter.get("triggers", [])
        
        print(f"\n{skill_id}:")
        print(f"  名称: {skill_def.name}")
        print(f"  类型: {skill_type}")
        print(f"  描述: {skill_def.description}")
        if triggers:
            print(f"  触发词: {triggers}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_get_process_skills()
    test_all_skills()
