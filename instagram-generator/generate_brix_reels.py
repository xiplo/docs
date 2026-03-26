#!/usr/bin/env python3
"""BRIX.UZ Reel Generator — generates all 8 viral reels.

Usage (on your server with internet access):
    pip install -r requirements.txt
    echo 'PIAPI_API_KEY=28160f0d460c2e3a1316b601bd8d58b37a0601784572935225435cda394e4ae9' >> .env
    python generate_brix_reels.py

This script:
  1. Generates images via PiAPI Flux (1080x1920)
  2. Animates them via PiAPI Seedance 2.0 (9:16 vertical)
  3. Saves all outputs to ./output/brix_reels/
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from clients.piapi import PiAPIClient
from brands.brix_uz import get_all_briefs, BrixBrandProfile


async def generate_reel(client: PiAPIClient, brief: dict, output_dir: Path) -> dict:
    """Generate a single reel: Flux image → Seedance 2.0 video."""
    brief_id = brief["id"]
    reel_dir = output_dir / brief_id
    reel_dir.mkdir(parents=True, exist_ok=True)

    result = {"id": brief_id, "topic": brief["topic"], "status": "pending"}

    try:
        # Step 1: Generate image via Flux
        print(f"\n  [{brief_id}] Step 1: Generating image via Flux...")
        img_result = await client.flux_text_to_image(
            prompt=brief["image_prompt"],
            width=1080,
            height=1920,
        )
        image_url = img_result.image_urls[0] if img_result.image_urls else ""
        if not image_url:
            raise RuntimeError("No image URL in Flux result")

        image_path = reel_dir / "image.png"
        await client.download(image_url, image_path)
        print(f"  [{brief_id}] Image saved: {image_path}")
        result["image_url"] = image_url
        result["image_path"] = str(image_path)

        # Step 2: Generate video via Seedance 2.0
        print(f"  [{brief_id}] Step 2: Generating video via Seedance 2.0...")
        vid_prompt = brief.get("video_prompt", brief["image_prompt"])
        vid_result = await client.seedance_image_to_video(
            image_url=image_url,
            prompt=vid_prompt,
            duration=int(brief["duration"]),
            aspect_ratio="9:16",
        )
        video_url = vid_result.video_urls[0] if vid_result.video_urls else ""
        if not video_url:
            raise RuntimeError("No video URL in Seedance result")

        video_path = reel_dir / "reel.mp4"
        await client.download(video_url, video_path)
        print(f"  [{brief_id}] Video saved: {video_path}")
        result["video_url"] = video_url
        result["video_path"] = str(video_path)

        # Save metadata
        meta = {
            **brief,
            "image_url": image_url,
            "video_url": video_url,
            "generated_at": datetime.now().isoformat(),
        }
        (reel_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False)
        )

        result["status"] = "completed"
        print(f"  [{brief_id}] DONE")

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        print(f"  [{brief_id}] FAILED: {e}")

    return result


async def main():
    profile = BrixBrandProfile()
    briefs = get_all_briefs()
    output_dir = Path("./output/brix_reels")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"  {profile.name} — Viral Reel Generator")
    print(f"  {profile.tagline_uz}")
    print(f"  {len(briefs)} reels to generate")
    print(f"  Pipeline: Flux (1080x1920) → Seedance 2.0 (9:16)")
    print(f"  Output: {output_dir}")
    print("=" * 65)

    client = PiAPIClient()
    if not client.configured:
        print("\n  ERROR: PIAPI_API_KEY not set. Add it to .env")
        return

    results = []
    for i, brief in enumerate(briefs, 1):
        print(f"\n--- Reel {i}/{len(briefs)}: {brief['topic'][:50]} ---")
        print(f"  Hook: {brief['hook']}")
        result = await generate_reel(client, brief, output_dir)
        results.append(result)

    await client.close()

    # Summary
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")

    print("\n" + "=" * 65)
    print(f"  Results: {completed} completed, {failed} failed")
    print("=" * 65)

    for r in results:
        icon = "OK" if r["status"] == "completed" else "FAIL"
        print(f"  [{icon}] {r['id']:<32} {r.get('error', '')[:40]}")

    # Save results
    results_file = output_dir / "results.json"
    results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n  Results saved: {results_file}")

    if completed > 0:
        print(f"\n  Next steps:")
        print(f"    1. Review videos in {output_dir}/")
        print(f"    2. Add voiceover: python main.py brix --generate <id>")
        print(f"    3. Post to Instagram: python main.py crosspost --content-id <id>")


if __name__ == "__main__":
    asyncio.run(main())
