"""Strategy Engine — AI-driven content planning and optimization.

The Strategy Engine:
  - Plans a weekly content calendar
  - Balances content types and categories
  - Uses analytics to optimize future posts
  - Adapts to time-of-day and day-of-week patterns
  - Manages content freshness and variation
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import structlog

from config import settings
from skills.analytics import AnalyticsSkills
from skills.audience import AudienceSkills, SEGMENTS

logger = structlog.get_logger(__name__)


@dataclass
class ContentSlot:
    """A planned content slot in the calendar."""

    day: str  # YYYY-MM-DD
    time: str  # HH:MM
    content_type: str
    category: str
    topic: str
    style_preset: str = "photorealistic"
    duration: str = "5"
    target_segment: str = "young_professionals"
    priority: int = 5  # 1-10, 10 = highest


# Day-of-week strategy
DAY_STRATEGY = {
    0: {  # Monday
        "theme": "Motivation Monday",
        "categories": ["motivational", "educational"],
        "energy": "high",
    },
    1: {  # Tuesday
        "theme": "Tips Tuesday",
        "categories": ["educational", "tech"],
        "energy": "moderate",
    },
    2: {  # Wednesday
        "theme": "Wisdom Wednesday",
        "categories": ["educational", "motivational"],
        "energy": "moderate",
    },
    3: {  # Thursday
        "theme": "Throwback Thursday",
        "categories": ["travel", "lifestyle", "fashion"],
        "energy": "moderate",
    },
    4: {  # Friday
        "theme": "Food Friday",
        "categories": ["recipe", "lifestyle"],
        "energy": "relaxed",
    },
    5: {  # Saturday
        "theme": "Style Saturday",
        "categories": ["fashion", "lifestyle", "product"],
        "energy": "high",
    },
    6: {  # Sunday
        "theme": "Story Sunday",
        "categories": ["travel", "motivational", "lifestyle"],
        "energy": "relaxed",
    },
}

# Category → content type mapping (what works best)
CATEGORY_CONTENT_MAP = {
    "motivational": ["reel", "image", "story"],
    "educational": ["carousel", "reel"],
    "product": ["reel", "carousel", "image"],
    "travel": ["reel", "carousel", "image"],
    "recipe": ["reel", "carousel"],
    "fashion": ["carousel", "reel", "image"],
    "tech": ["carousel", "reel"],
    "lifestyle": ["reel", "story", "image"],
    "humor": ["reel", "story"],
}

# Topic pools by category (Uzbek-focused)
TOPIC_POOLS = {
    "motivational": [
        "Muvaffaqiyat qoidalari",
        "Ertalab erta turish foydasi",
        "Maqsadga erishish yo'llari",
        "Pul topish sirlari",
        "O'zini rivojlantirish",
        "Kuchli iroda qanday shakllanadi",
        "Liderlik sifatlari",
        "Vaqtni boshqarish san'ati",
        "Muammolarni yechish usullari",
        "Ijobiy fikrlash kuchi",
    ],
    "educational": [
        "Python dasturlash asoslari",
        "Ingliz tilini tez o'rganish",
        "Marketing strategiyalari",
        "Moliyaviy savodxonlik",
        "Sog'lom ovqatlanish qoidalari",
        "Sun'iy intellekt haqida",
        "Biznes boshlash bosqichlari",
        "Veb-dizayn asoslari",
        "Ijtimoiy tarmoq marketingi",
        "Freelance ishlash sirlari",
    ],
    "product": [
        "Yangi mahsulot taqdimoti",
        "Maxsus chegirma e'loni",
        "Mijozlar sharhlari",
        "Mahsulot taqqoslash",
        "Qanday tanlash kerak",
    ],
    "travel": [
        "Samarqand — Sharq durdonasi",
        "Buxoro qadimiy shahri",
        "Xiva — ochiq osmon ostidagi muzey",
        "Chimyon tog'lari",
        "Chorvoq ko'li dam olish",
        "Farg'ona vodiysi go'zalligi",
        "Nukus san'at muzeyi",
        "Ipak yo'li tarixi",
        "O'zbekiston milliy bog'lari",
        "Toshkent zamonaviy shahri",
    ],
    "recipe": [
        "An'anaviy palov tayyorlash",
        "Somsa pishirish sirlari",
        "Lag'mon tayyorlash",
        "Manti retsepti",
        "Shashlik sirlari",
        "Halim tayyorlash",
        "Chuchvara retsepti",
        "Non yopish an'anasi",
        "Norin tayyorlash",
        "Dimlama retsepti",
    ],
    "fashion": [
        "Atlas ko'ylak dizaynlari",
        "Zamonaviy o'zbek modasi",
        "Erkaklar uslubi 2024",
        "Ayollar kiyim kombinatsiyalari",
        "Aksessuarlar tanlash",
    ],
    "tech": [
        "Eng yaxshi mobil ilovalar",
        "AI toollar kundalik hayotda",
        "Kiberhavfsizlik maslahatlar",
        "Smartfon sirlari",
        "Yangi texnologiya trendlari",
    ],
    "lifestyle": [
        "Ertalabki odat",
        "Meditatsiya boshlash",
        "Uy tozalash lifehacklari",
        "Sog'lom uxlash qoidalari",
        "Stress boshqarish usullari",
    ],
    "humor": [
        "IT mutaxassisning kundalik hayoti",
        "O'zbek oilasidagi vaziyatlar",
        "Talabalar hayoti",
        "Ishga kechikish sabablari",
        "Online xarid qilish voqealari",
    ],
}


class StrategyEngine:
    """Plans and optimizes content strategy."""

    def __init__(self, timezone: str | None = None) -> None:
        self.tz = ZoneInfo(timezone or settings.timezone)

    def plan_week(self, posts_per_day: int = 3) -> list[ContentSlot]:
        """Plan a full week of content slots."""
        today = datetime.now(self.tz).date()
        post_times = ["09:00", "13:00", "18:00"][:posts_per_day]

        slots = []
        used_topics: set[str] = set()

        for day_offset in range(7):
            date = today + timedelta(days=day_offset)
            day_of_week = date.weekday()
            day_config = DAY_STRATEGY[day_of_week]

            for i, post_time in enumerate(post_times):
                category = self._pick_category(day_config["categories"], i)
                content_type = self._pick_content_type(category, post_time)
                topic = self._pick_topic(category, used_topics)
                used_topics.add(topic)
                style = self._pick_style(category)
                duration = "10" if category in ("travel", "recipe") else "5"
                segment = self._pick_segment(category)

                slot = ContentSlot(
                    day=date.isoformat(),
                    time=post_time,
                    content_type=content_type,
                    category=category,
                    topic=topic,
                    style_preset=style,
                    duration=duration,
                    target_segment=segment,
                    priority=self._calculate_priority(category, post_time),
                )
                slots.append(slot)

        logger.info("strategy.planned_week", total_slots=len(slots))
        return slots

    def plan_day(self, posts_per_day: int = 3) -> list[ContentSlot]:
        """Plan today's content slots."""
        full_week = self.plan_week(posts_per_day)
        today = datetime.now(self.tz).date().isoformat()
        return [s for s in full_week if s.day == today]

    def suggest_topic(self, category: str) -> str:
        """Suggest a single topic for a category."""
        topics = TOPIC_POOLS.get(category, TOPIC_POOLS["motivational"])
        return random.choice(topics)

    def _pick_category(self, preferred: list[str], slot_index: int) -> str:
        if slot_index < len(preferred):
            return preferred[slot_index]
        return random.choice(preferred)

    def _pick_content_type(self, category: str, post_time: str) -> str:
        options = CATEGORY_CONTENT_MAP.get(category, ["reel"])
        # Morning = reels, afternoon = carousels, evening = mixed
        hour = int(post_time.split(":")[0])
        if hour < 12:
            # Prefer reels in morning
            if "reel" in options:
                return "reel"
        elif hour < 15:
            # Prefer carousels in afternoon
            if "carousel" in options:
                return "carousel"
        return random.choice(options)

    def _pick_topic(self, category: str, used: set[str]) -> str:
        topics = TOPIC_POOLS.get(category, TOPIC_POOLS["motivational"])
        available = [t for t in topics if t not in used]
        if not available:
            available = topics
        return random.choice(available)

    def _pick_style(self, category: str) -> str:
        styles = {
            "motivational": "cinematic",
            "educational": "flat_design",
            "product": "photorealistic",
            "travel": "photorealistic",
            "recipe": "photorealistic",
            "fashion": "photorealistic",
            "tech": "3d_render",
            "lifestyle": "photorealistic",
            "humor": "illustration",
        }
        return styles.get(category, "photorealistic")

    def _pick_segment(self, category: str) -> str:
        segments = AudienceSkills.get_segment_for_category(category)
        if segments:
            return segments[0].name
        return "young_professionals"

    def _calculate_priority(self, category: str, post_time: str) -> int:
        """Higher priority for best-performing categories and peak times."""
        priority = 5

        best = AnalyticsSkills.get_best_performing_category()
        if best and category == best:
            priority += 2

        # Peak hours get higher priority
        hour = int(post_time.split(":")[0])
        if hour in [9, 13, 18]:
            priority += 1

        return min(priority, 10)
