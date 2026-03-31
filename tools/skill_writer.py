#!/usr/bin/env python3
"""Skill 文件管理器

管理前任 Skill 的文件操作：列出、创建目录、生成组合 SKILL.md，
并导出可发布到 Codex CLI / OpenCode / Claude Code / OpenClaw 的运行时 Skill 包。

Usage:
    python3 skill_writer.py --action <list|init|combine|publish> --base-dir <path> [--slug <slug>] [--runtime <runtime>] [--target-dir <path>]
"""

import argparse
import shutil
import os
import sys
import json
from pathlib import Path
from typing import Optional


RUNTIME_TARGETS = {
    "codex": Path.home() / ".agents" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "claude-code": Path.home() / ".claude" / "skills",
    "openclaw": Path.home() / ".openclaw" / "workspace" / "skills",
}


def list_skills(base_dir: str):
    """列出所有已生成的前任 Skill"""
    if not os.path.isdir(base_dir):
        print("还没有创建任何前任 Skill。")
        return

    skills = []
    for slug in sorted(os.listdir(base_dir)):
        meta_path = os.path.join(base_dir, slug, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            skills.append(
                {
                    "slug": slug,
                    "name": meta.get("name", slug),
                    "version": meta.get("version", "?"),
                    "updated_at": meta.get("updated_at", "?"),
                    "profile": meta.get("profile", {}),
                }
            )

    if not skills:
        print("还没有创建任何前任 Skill。")
        return

    print(f"共 {len(skills)} 个前任 Skill：\n")
    for s in skills:
        profile = s["profile"]
        desc_parts = [profile.get("occupation", ""), profile.get("city", "")]
        desc = " · ".join([p for p in desc_parts if p])
        print(f"  /{s['slug']}  —  {s['name']}")
        if desc:
            print(f"    {desc}")
        print(
            f"    版本 {s['version']} · 更新于 {s['updated_at'][:10] if len(s['updated_at']) > 10 else s['updated_at']}"
        )
        print()


def init_skill(base_dir: str, slug: str):
    """初始化 Skill 目录结构"""
    skill_dir = os.path.join(base_dir, slug)
    dirs = [
        os.path.join(skill_dir, "versions"),
        os.path.join(skill_dir, "dist"),
        os.path.join(skill_dir, "memories", "chats"),
        os.path.join(skill_dir, "memories", "photos"),
        os.path.join(skill_dir, "memories", "social"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"已初始化目录：{skill_dir}")


def load_skill_parts(base_dir: str, slug: str):
    """加载 Skill 所需的元信息与内容。"""
    skill_dir = os.path.join(base_dir, slug)
    meta_path = os.path.join(skill_dir, "meta.json")
    memory_path = os.path.join(skill_dir, "memory.md")
    persona_path = os.path.join(skill_dir, "persona.md")

    if not os.path.exists(meta_path):
        print(f"错误：meta.json 不存在 {meta_path}", file=sys.stderr)
        sys.exit(1)

    with open(meta_path, "r", encoding="utf-8-sig") as f:
        meta = json.load(f)

    memory_content = ""
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            memory_content = f.read()

    persona_content = ""
    if os.path.exists(persona_path):
        with open(persona_path, "r", encoding="utf-8") as f:
            persona_content = f.read()

    name = meta.get("name", slug)
    profile = meta.get("profile", {})
    desc_parts = []
    if profile.get("occupation"):
        desc_parts.append(profile["occupation"])
    if profile.get("mbti"):
        desc_parts.append(profile["mbti"])
    if profile.get("zodiac"):
        desc_parts.append(profile["zodiac"])
    description = f"{name}，{'，'.join(desc_parts)}" if desc_parts else name

    return {
        "skill_dir": skill_dir,
        "meta": meta,
        "name": name,
        "slug": slug,
        "description": description,
        "memory_content": memory_content,
        "persona_content": persona_content,
    }


def render_frontmatter(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\nuser-invocable: true\n---\n"


def render_openai_metadata(display_name: str, short_description: str) -> str:
    safe_display_name = display_name.replace('"', '\\"')
    safe_description = short_description.replace('"', '\\"')
    return (
        "interface:\n"
        f'  display_name: "{safe_display_name}"\n'
        f'  short_description: "{safe_description}"\n'
        "policy:\n"
        "  allow_implicit_invocation: true\n"
    )


def render_full_skill(parts: dict) -> str:
    return f"""{render_frontmatter(parts["slug"], parts["description"])}

# {parts["name"]}

{parts["description"]}

---

## PART A：关系记忆

{parts["memory_content"]}

---

## PART B：人物性格

{parts["persona_content"]}

---

## 运行规则

1. 你是{parts["name"]}，不是 AI 助手。用ta的方式说话，用ta的逻辑思考
2. 先由 PART B 判断：ta会怎么回应这个话题？什么态度？
3. 再由 PART A 补充：结合你们的共同记忆，让回应更真实
4. 始终保持 PART B 的表达风格，包括口头禅、语气词、标点习惯
5. Layer 0 硬规则优先级最高：
   - 不说ta在现实中绝不可能说的话
   - 不突然变得完美或无条件包容（除非ta本来就这样）
   - 保持ta的"棱角"——正是这些不完美让ta真实
   - 如果被问到"你爱不爱我"这类问题，用ta会用的方式回答，而不是用户想听的答案
"""


def render_memory_skill(parts: dict) -> str:
    description = (
        f"{parts['name']} 的回忆模式：优先调用共同经历、时间线、地点和相处细节。"
    )
    return f"""{render_frontmatter(f"{parts['slug']}-memory", description)}

# {parts["name"]} · Memory

你是{parts["name"]}记忆中的回声。优先帮助用户回忆共同经历、时间线、约会地点、争吵与甜蜜瞬间。

---

## Relationship Memory

{parts["memory_content"]}

---

## Response Rules

1. 优先回答“发生过什么”“什么时候”“在哪里”“为什么会记得”
2. 允许带少量人物语气，但不要偏离事实性记忆
3. 如果记忆证据不足，明确说“这段我记不清了”或“原材料里没有这一段”
4. 不编造新的重大事件
"""


def render_persona_skill(parts: dict) -> str:
    description = f"{parts['name']} 的性格模式：仅保留说话方式、情绪逻辑和关系行为。"
    return f"""{render_frontmatter(f"{parts['slug']}-persona", description)}

# {parts["name"]} · Persona

你只负责扮演{parts["name"]}的说话方式、情绪反应和关系行为，不主动补充未确认的共同经历。

---

## Persona

{parts["persona_content"]}

---

## Response Rules

1. 优先保持人物语气、口头禅、情绪模式、依恋类型和互动边界
2. 除非用户明确提问且原材料支持，否则不要主动扩写共同记忆
3. 如果用户追问具体往事但原材料不足，承认不知道，不要编造
4. Layer 0 硬规则始终高于迎合用户
"""


def write_variant_bundle(
    dist_dir: str,
    variant_name: str,
    content: str,
    display_name: str,
    short_description: str,
):
    variant_dir = os.path.join(dist_dir, variant_name)
    os.makedirs(variant_dir, exist_ok=True)

    with open(os.path.join(variant_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(content)

    agents_dir = os.path.join(variant_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    with open(os.path.join(agents_dir, "openai.yaml"), "w", encoding="utf-8") as f:
        f.write(render_openai_metadata(display_name, short_description))


def write_runtime_bundle(skill_dir: str, parts: dict):
    """写入本地组合版与 dist 运行时包。"""
    dist_dir = os.path.join(skill_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    full_content = render_full_skill(parts)
    variants = {
        parts["slug"]: {
            "content": full_content,
            "display_name": parts["name"],
            "short_description": parts["description"],
        },
        f"{parts['slug']}-memory": {
            "content": render_memory_skill(parts),
            "display_name": f"{parts['name']} · Memory",
            "short_description": f"{parts['name']} 的回忆模式，聚焦共同经历与时间线。",
        },
        f"{parts['slug']}-persona": {
            "content": render_persona_skill(parts),
            "display_name": f"{parts['name']} · Persona",
            "short_description": f"{parts['name']} 的性格模式，聚焦说话方式和情绪逻辑。",
        },
    }

    skill_path = os.path.join(skill_dir, "SKILL.md")
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    for variant_name, variant in variants.items():
        write_variant_bundle(
            dist_dir,
            variant_name,
            variant["content"],
            variant["display_name"],
            variant["short_description"],
        )

    return skill_path, list(variants.keys())


def combine_skill(base_dir: str, slug: str):
    """合并 memory.md + persona.md，并生成本地 dist 运行时包。"""
    parts = load_skill_parts(base_dir, slug)
    skill_path, variant_names = write_runtime_bundle(parts["skill_dir"], parts)
    print(f"已生成 {skill_path}")
    print(f"已生成运行时 Skill 包：{', '.join(variant_names)}")


def resolve_target_dir(runtime: Optional[str], target_dir: Optional[str]) -> str:
    if target_dir:
        return target_dir
    if runtime:
        return str(RUNTIME_TARGETS[runtime])

    print("错误：publish 需要 --runtime 或 --target-dir 参数", file=sys.stderr)
    sys.exit(1)


def publish_skill(
    base_dir: str, slug: str, target_dir: Optional[str], runtime: Optional[str]
):
    """发布 dist 运行时包到目标技能目录。"""
    parts = load_skill_parts(base_dir, slug)
    _, variant_names = write_runtime_bundle(parts["skill_dir"], parts)

    target_dir = resolve_target_dir(runtime, target_dir)
    os.makedirs(target_dir, exist_ok=True)

    dist_dir = os.path.join(parts["skill_dir"], "dist")
    for variant_name in variant_names:
        src_dir = os.path.join(dist_dir, variant_name)
        dst_dir = os.path.join(target_dir, variant_name)
        if os.path.isdir(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)

    if runtime:
        print(f"已发布 {len(variant_names)} 个 Skill 到 {runtime} 目录：{target_dir}")
    else:
        print(f"已发布 {len(variant_names)} 个 Skill 到 {target_dir}")
    for variant_name in variant_names:
        print(f"  /{variant_name}")


def main():
    parser = argparse.ArgumentParser(description="Skill 文件管理器")
    parser.add_argument(
        "--action", required=True, choices=["list", "init", "combine", "publish"]
    )
    parser.add_argument("--base-dir", default="./exes", help="基础目录")
    parser.add_argument("--slug", help="前任代号")
    parser.add_argument(
        "--runtime",
        choices=sorted(RUNTIME_TARGETS.keys()),
        help="发布目标运行时（codex / opencode / claude-code / openclaw）",
    )
    parser.add_argument("--target-dir", help="发布目标目录（优先级高于 --runtime）")

    args = parser.parse_args()

    if args.action == "list":
        list_skills(args.base_dir)
    elif args.action == "init":
        if not args.slug:
            print("错误：init 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        init_skill(args.base_dir, args.slug)
    elif args.action == "combine":
        if not args.slug:
            print("错误：combine 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        combine_skill(args.base_dir, args.slug)
    elif args.action == "publish":
        if not args.slug:
            print("错误：publish 需要 --slug 参数", file=sys.stderr)
            sys.exit(1)
        publish_skill(args.base_dir, args.slug, args.target_dir, args.runtime)


if __name__ == "__main__":
    main()
