import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not installed. Run: pip install pyyaml")


class SkillDefinition:
    def __init__(self, skill_dir, frontmatter, instructions):
        self.skill_dir = skill_dir
        self.frontmatter = frontmatter
        self.instructions = instructions
        self.id = frontmatter.get("name", skill_dir.name)
        self.name = frontmatter.get("display_name", self.id)
        self.description = frontmatter.get("description", "")
        self.version = str(frontmatter.get("version", "1.0"))
        self.enabled = frontmatter.get("enabled", True)
        self.triggers = frontmatter.get("triggers", [])
        self.pipeline = frontmatter.get("pipeline", [])
        self.output = frontmatter.get("output", {})

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.id,
            "display_name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "triggers": self.triggers,
            "pipeline": self.pipeline,
            "output": self.output,
            "instructions": self.instructions,
            "skill_type": self.frontmatter.get("skill_type", "qa"),
            "nodes": self.frontmatter.get("nodes", []),
            "_skill_dir": str(self.skill_dir),
        }

    def __repr__(self):
        return f"<SkillDefinition id={self.id!r} version={self.version!r}>"


def _parse_frontmatter(content):
    content = content.strip()
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    yaml_str = content[3:end].strip()
    body = content[end + 4 :].strip()
    if YAML_AVAILABLE:
        try:
            data = yaml.safe_load(yaml_str) or {}
        except Exception as e:
            logger.error("YAML parse error: %s", e)
            data = {}
    else:
        data = _simple_yaml_parse(yaml_str)
    return data, body


def _simple_yaml_parse(yaml_str):
    result = {}
    for line in yaml_str.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip()
            if val.lower() == "true":
                result[key.strip()] = True
            elif val.lower() == "false":
                result[key.strip()] = False
            elif val.startswith('"') and val.endswith('"'):
                result[key.strip()] = val[1:-1]
            elif val.isdigit():
                result[key.strip()] = int(val)
            else:
                result[key.strip()] = val
    return result


class SkillLoader:
    def __init__(self, skills_dir):
        self.skills_dir = Path(skills_dir)
        self._cache = {}

    def load_all(self):
        if not self.skills_dir.exists():
            logger.warning("Skills dir not found: %s", self.skills_dir)
            return {}
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        skill = self._load_one(skill_dir)
                        self._cache[skill.id] = skill
                        logger.info("Loaded skill: %s (v%s)", skill.id, skill.version)
                    except Exception as e:
                        logger.error("Failed to load skill [%s]: %s", skill_dir.name, e)
        return self._cache

    def get(self, skill_id):
        if skill_id not in self._cache:
            skill_dir = self.skills_dir / skill_id
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    skill = self._load_one(skill_dir)
                    self._cache[skill.id] = skill
                except Exception as e:
                    logger.error("Failed to load skill [%s]: %s", skill_id, e)
                    return None
        return self._cache.get(skill_id)

    def reload(self, skill_id=None):
        if skill_id:
            self._cache.pop(skill_id, None)
        else:
            self._cache.clear()
        self.load_all()

    def list_skills(self):
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "version": s.version,
            }
            for s in self._cache.values()
        ]

    def _load_one(self, skill_dir):
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        frontmatter, instructions = _parse_frontmatter(content)
        return SkillDefinition(skill_dir, frontmatter, instructions)
