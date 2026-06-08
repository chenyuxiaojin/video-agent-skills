#!/usr/bin/env python3
"""
批量图片生成脚本 — 读取 storyboard.json，调用 GPTIMG2（gpt-image-2，OpenAI 兼容 API）生成 2K 图片

用法：
    python generate_images.py <project_dir> [--style <风格文件>] [--concurrency <并发数>] [--aspect-ratio <比例>]

示例：
    python generate_images.py ~/CC视频/projects/my-video
    python generate_images.py ~/CC视频/projects/my-video --style tech --concurrency 3

环境变量（优先读环境变量，否则从 密钥存储/.env 解析）：
    GPTIMG2_BASE_URL — GPTIMG2 服务基址（如 https://api.chatgpt-code.com，末尾不带 /v1）
    GPTIMG2_API_KEY  — GPTIMG2 API 密钥
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

SCRIPT_DIR = Path(__file__).parent
STYLES_DIR = SCRIPT_DIR.parent / "styles"

GPTIMG2_MODEL = "gpt-image-2"
ENV_FILE = Path("~/项目/自己的应用/密钥存储/.env").expanduser()

# 宽高比 → GPTIMG2 2K 尺寸映射（边长对齐 16 的倍数）
ASPECT_RATIO_SIZES = {
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "1:1": "2048x2048",
    "4:3": "2048x1536",
    "3:4": "1536x2048",
}
DEFAULT_SIZE = "2560x1440"  # 16:9 兜底


def load_gptimg2():
    """读取 GPTIMG2 配置：环境变量优先，否则从 密钥存储/.env 解析。

    返回 (base, key)，base 已规整为不带 /v1 的形式（拼 URL 时自己加 /v1/...）。
    """
    base = os.environ.get("GPTIMG2_BASE_URL")
    key = os.environ.get("GPTIMG2_API_KEY")
    if (not base or not key) and ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln.startswith("#") or "=" not in ln:
                    continue
                if ln.startswith("GPTIMG2_BASE_URL=") and not base:
                    base = ln.split("=", 1)[1].strip()
                elif ln.startswith("GPTIMG2_API_KEY=") and not key:
                    key = ln.split("=", 1)[1].strip()
    if not base or not key:
        return None, None
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]
    return base, key


def size_for_aspect_ratio(aspect_ratio: str) -> str:
    """把宽高比映射到 GPTIMG2 的 2K 尺寸字符串，未知比例兜底为 16:9。"""
    return ASPECT_RATIO_SIZES.get(aspect_ratio.strip(), DEFAULT_SIZE)


def load_style(style_name: str) -> str:
    """加载风格指令文件"""
    style_path = STYLES_DIR / f"{style_name}.txt"
    if not style_path.exists():
        available = [f.stem for f in STYLES_DIR.glob("*.txt")]
        print(f"⚠️  风格 '{style_name}' 不存在，可用风格：{available}")
        print(f"   使用默认风格 'default'")
        style_path = STYLES_DIR / "default.txt"
        if not style_path.exists():
            return ""
    return style_path.read_text(encoding="utf-8").strip()


def load_storyboard(project_dir: Path) -> list:
    """读取分镜 JSON"""
    json_path = project_dir / "storyboard.json"
    if not json_path.exists():
        print(f"错误：找不到 {json_path}")
        print("请先运行 generate_storyboard.py 生成分镜表")
        sys.exit(1)
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def generate_single_image(
    shot: dict,
    style_prefix: str,
    aspect_ratio: str,
    output_dir: Path,
    base_url: str,
    api_key: str,
) -> dict:
    """为单个镜头生成图片（GPTIMG2 / gpt-image-2，纯文生图），返回结果字典"""
    shot_num = shot.get("shot_number", 0)
    image_prompt = shot.get("image_prompt", "")
    filename = f"{str(shot_num).zfill(3)}.png"
    output_path = output_dir / filename

    # 组合 prompt：风格前缀 + 镜头 prompt + 宽高比
    full_prompt = f"{style_prefix}\n\n{image_prompt}\n\nAspect ratio: {aspect_ratio}. High quality, detailed."

    result = {
        "shot_number": shot_num,
        "file": f"visuals/{filename}",
        "status": "pending",
        "prompt": image_prompt,
    }

    size = size_for_aspect_ratio(aspect_ratio)
    gen_url = f"{base_url}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GPTIMG2_MODEL,
        "prompt": full_prompt,
        "size": size,
        "n": 1,
        "response_format": "url",
    }

    max_retries = 2
    for attempt in range(max_retries):
        try:
            resp = requests.post(gen_url, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            resp_data = resp.json()

            # OpenAI 兼容响应：data[0].url 拿到图片 url，再下载字节落地
            image_url = resp_data["data"][0]["url"]
            img_resp = requests.get(image_url, timeout=120)
            img_resp.raise_for_status()
            output_path.write_bytes(img_resp.content)

            result["status"] = "success"
            return result

        except (requests.RequestException, RuntimeError, KeyError, IndexError, ValueError) as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                result["status"] = "failed"
                result["error"] = str(e)
                return result

    return result


def generate_report(results: list, project_dir: Path) -> str:
    """生成素材报告 markdown"""
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    lines = [
        "# 素材生成报告",
        "",
        "## 统计",
        "",
        f"- 总镜头数：{total}",
        f"- 生成成功：{success}",
        f"- 生成失败：{failed}",
        f"- 后期制作（跳过）：{skipped}",
        "",
        "## 明细",
        "",
        "| 镜头 | 状态 | 文件 | 备注 |",
        "|------|------|------|------|",
    ]

    for r in sorted(results, key=lambda x: x["shot_number"]):
        num = str(r["shot_number"]).zfill(3)
        status_icon = {"success": "✅", "failed": "❌", "skipped": "📋"}.get(r["status"], "?")
        file_col = r.get("file", "-")
        note = r.get("error", r.get("skip_reason", ""))
        lines.append(f"| {num} | {status_icon} | {file_col} | {note} |")

    if failed > 0:
        lines.extend([
            "",
            "## 失败镜头（需人工处理）",
            "",
        ])
        for r in results:
            if r["status"] == "failed":
                lines.append(f"- 镜头 {str(r['shot_number']).zfill(3)}: {r.get('error', '未知错误')}")
                lines.append(f"  Prompt: {r.get('prompt', '')}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="批量生成图片素材")
    parser.add_argument("project_dir", help="项目目录路径")
    parser.add_argument("--style", default="default", help="风格名称（对应 styles/ 下的文件名，默认：default）")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数（默认：5）")
    parser.add_argument("--aspect-ratio", default="16:9", help="宽高比（默认：16:9）")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        print(f"错误：项目目录不存在 {project_dir}")
        sys.exit(1)

    base_url, api_key = load_gptimg2()
    if not base_url or not api_key:
        print("错误：缺少 GPTIMG2 配置（环境变量 GPTIMG2_BASE_URL / GPTIMG2_API_KEY，")
        print(f"      或 {ENV_FILE} 中对应键）")
        sys.exit(1)

    # 1. 读取分镜
    print("📖 读取 storyboard.json...")
    shots = load_storyboard(project_dir)

    # 2. 加载风格
    style_prefix = load_style(args.style)
    if style_prefix:
        print(f"🎨 使用风格：{args.style}")

    # 3. 创建输出目录
    visuals_dir = project_dir / "visuals"
    visuals_dir.mkdir(exist_ok=True)

    # 4. 过滤镜头
    to_generate = []
    results = []
    for shot in shots:
        if shot.get("is_post_production"):
            results.append({
                "shot_number": shot.get("shot_number", 0),
                "file": None,
                "status": "skipped",
                "skip_reason": f"后期制作 ({shot.get('asset_type', '')})",
            })
        else:
            to_generate.append(shot)

    size = size_for_aspect_ratio(args.aspect_ratio)
    print(f"🖼️  需要生成 {len(to_generate)} 张图片（跳过 {len(results)} 个后期镜头）")
    print(f"   模型：{GPTIMG2_MODEL} | 比例：{args.aspect_ratio} → 尺寸：{size}")

    # 5. 并发生成
    print(f"🚀 开始生成（并发数：{args.concurrency}）...")
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {}
        for shot in to_generate:
            future = executor.submit(
                generate_single_image,
                shot, style_prefix, args.aspect_ratio, visuals_dir, base_url, api_key,
            )
            futures[future] = shot.get("shot_number", 0)

        for future in as_completed(futures):
            shot_num = futures[future]
            try:
                result = future.result()
                results.append(result)
                icon = "✅" if result["status"] == "success" else "❌"
                print(f"   {icon} 镜头 {str(shot_num).zfill(3)}: {result['status']}")
            except Exception as e:
                results.append({
                    "shot_number": shot_num,
                    "status": "failed",
                    "error": str(e),
                })
                print(f"   ❌ 镜头 {str(shot_num).zfill(3)}: {e}")

    # 6. 生成报告
    report = generate_report(results, project_dir)
    report_path = project_dir / "visual-report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n✅ visual-report.md 已生成 → {report_path}")

    # 7. 生成 visual-timeline.json
    timeline = {
        "video_specs": {
            "resolution": "1920x1080",
            "fps": 30,
            "aspect_ratio": args.aspect_ratio,
        },
        "visuals": [],
    }

    for shot in sorted(shots, key=lambda x: x.get("shot_number", 0)):
        shot_num = shot.get("shot_number", 0)
        is_post = shot.get("is_post_production", False)
        matching = [r for r in results if r["shot_number"] == shot_num]
        status = matching[0]["status"] if matching else "unknown"

        # 解析时间范围
        time_range = shot.get("time_range", "0:00-0:00")
        parts = time_range.split("-")
        start_str = parts[0].strip() if len(parts) >= 1 else "0:00"
        end_str = parts[1].strip() if len(parts) >= 2 else start_str

        def parse_time(t: str) -> float:
            segments = t.split(":")
            if len(segments) == 2:
                return int(segments[0]) * 60 + float(segments[1])
            elif len(segments) == 3:
                return int(segments[0]) * 3600 + int(segments[1]) * 60 + float(segments[2])
            return 0.0

        start = parse_time(start_str)
        end = parse_time(end_str)

        entry = {
            "shot": str(shot_num).zfill(3),
            "file": f"visuals/{str(shot_num).zfill(3)}.png" if not is_post and status == "success" else None,
            "description": shot.get("image_prompt", ""),
            "start_time": start,
            "end_time": end,
            "duration": round(end - start, 2),
            "asset_type": shot.get("asset_type", ""),
            "acquire_method": "post_production" if is_post else "ai_generate",
            "mood": shot.get("mood", ""),
        }
        if is_post:
            entry["editor_note"] = shot.get("image_prompt", "")

        timeline["visuals"].append(entry)

    timeline["total_duration"] = max((v["end_time"] for v in timeline["visuals"]), default=0)

    timeline_path = project_dir / "visual-timeline.json"
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ visual-timeline.json 已生成 → {timeline_path}")

    # 8. 汇总
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    print(f"\n📊 生成汇总：成功 {success_count} / 失败 {failed_count} / 跳过 {len(shots) - len(to_generate)}")
    if failed_count > 0:
        print(f"⚠️  有 {failed_count} 个镜头生成失败，请查看 visual-report.md")


if __name__ == "__main__":
    main()
