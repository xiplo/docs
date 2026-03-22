"""Trending topics — discover and capitalize on trending content.

Sources:
  - Instagram Explore trends (via hashtag volume tracking)
  - Internal analytics (what's working for us)
  - Seasonal/calendar events (Uzbek holidays, global events)
  - Category-specific trend cycles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TrendingTopic:
    """A currently trending topic or theme."""

    name: str
    category: str
    relevance_score: float  # 0.0 - 1.0
    hashtags: list[str] = field(default_factory=list)
    suggested_hook: str = ""
    source: str = ""  # calendar, analytics, seasonal
    expires: str = ""  # ISO date when trend loses relevance


# =================================================================
# Uzbek calendar events and seasonal content
# =================================================================

UZBEK_CALENDAR_EVENTS = [
    # National holidays
    {"name": "Yangi yil", "date": "01-01", "duration": 3, "category": "lifestyle",
     "hashtags": ["yangiyil", "bayram", "yangi_yil_2026"]},
    {"name": "Xotin-qizlar kuni", "date": "03-08", "category": "motivational",
     "hashtags": ["8mart", "xotinqizlarkuni", "ayollar"]},
    {"name": "Navro'z", "date": "03-21", "duration": 2, "category": "recipe",
     "hashtags": ["navroz", "bahorbayrami", "sumalak", "navroz2026"]},
    {"name": "Xotira va qadrlash kuni", "date": "05-09", "category": "motivational",
     "hashtags": ["9may", "xotirakuni"]},
    {"name": "Mustaqillik kuni", "date": "09-01", "duration": 2, "category": "travel",
     "hashtags": ["mustaqillik", "1sentabr", "uzbekiston"]},
    {"name": "O'qituvchilar kuni", "date": "10-01", "category": "educational",
     "hashtags": ["uqituvchilarkuni", "muallim", "ustoz"]},
    {"name": "Konstitutsiya kuni", "date": "12-08", "category": "educational",
     "hashtags": ["konstitutsiyakuni", "qonun"]},

    # Religious (approximate, varies yearly)
    {"name": "Ro'za hayit", "date": "03-30", "duration": 3, "category": "lifestyle",
     "hashtags": ["rozahayit", "hayit", "ramazon"]},
    {"name": "Qurbon hayit", "date": "06-06", "duration": 4, "category": "lifestyle",
     "hashtags": ["qurbonhayit", "hayit", "qurbon"]},

    # Seasonal
    {"name": "Bahor mavsumi", "date": "03-15", "duration": 14, "category": "travel",
     "hashtags": ["bahor", "tabiat", "uzbekiston"]},
    {"name": "Yoz mavsumi", "date": "06-01", "duration": 30, "category": "travel",
     "hashtags": ["yoz", "sayohat", "dam_olish"]},
    {"name": "Maktab mavsumi", "date": "09-01", "duration": 7, "category": "educational",
     "hashtags": ["maktab", "talaba", "uqish"]},
    {"name": "Kuz mavsumi", "date": "10-01", "duration": 14, "category": "recipe",
     "hashtags": ["kuz", "hosil", "taom"]},
]

# =================================================================
# Evergreen trend cycles (repeat annually)
# =================================================================

MONTHLY_TRENDS = {
    1: [  # January
        TrendingTopic("Yangi yil maqsadlari", "motivational", 0.9,
                      ["yangi_yil", "maqsad", "reja"], "2026-yilda nimaga erishasiz?"),
        TrendingTopic("Qishki taomlar", "recipe", 0.7,
                      ["qishki_taom", "issiq_taom"], "Sovuq kunlarda issiq taom!"),
    ],
    2: [
        TrendingTopic("Sevgi kuni", "lifestyle", 0.8,
                      ["valentinka", "sevgi", "muhabbat"], "Sevgingizni namoyon qiling"),
    ],
    3: [
        TrendingTopic("Navro'z tayyorgarligi", "recipe", 0.95,
                      ["navroz", "sumalak", "halim"], "Navro'z dasturxoni sirlar"),
        TrendingTopic("Bahor tozalash", "lifestyle", 0.6,
                      ["bahor_tozalash", "uyni_tozalash"], "Bahor — yangilanish vaqti"),
    ],
    4: [
        TrendingTopic("Sog'lom turmush", "educational", 0.7,
                      ["salomatlik", "sport", "parhez"], "Bahordan boshlab sog'lom yashing"),
    ],
    5: [
        TrendingTopic("Ona kuniga tayyorgarlik", "lifestyle", 0.8,
                      ["onalar_kuni", "oila"], "Onangizga eng yaxshi sovg'a"),
    ],
    6: [
        TrendingTopic("Yozgi sayohat", "travel", 0.9,
                      ["yoz", "sayohat", "plaj", "toglar"], "Eng yaxshi yozgi yo'nalishlar"),
        TrendingTopic("Yozgi taomlar", "recipe", 0.7,
                      ["yozgi_taom", "salat", "sovuq_ichimlik"], "Issiq kunlarda sovuq taomlar"),
    ],
    7: [
        TrendingTopic("Dam olish mavsumi", "travel", 0.8,
                      ["dam_olish", "ta_til", "oila_bilan"], "Eng yaxshi dam olish joylari"),
    ],
    8: [
        TrendingTopic("Maktabga tayyorgarlik", "educational", 0.85,
                      ["maktab", "1sentabr", "tayyorgarlik"], "Maktab mavsumiga tayyor!"),
    ],
    9: [
        TrendingTopic("Mustaqillik bayrami", "motivational", 0.95,
                      ["mustaqillik", "uzbekiston", "vatan"], "O'zbekiston — buyuk kelajak"),
        TrendingTopic("Kuzgi moda", "fashion", 0.7,
                      ["kuz_modasi", "stil", "kiyim"], "Bu kuzda nima kiyamiz?"),
    ],
    10: [
        TrendingTopic("O'qituvchilar kuni", "educational", 0.85,
                      ["ustoz", "muallim", "rahmat"], "Ustozlarga minnatdorchilik"),
        TrendingTopic("Kuzgi oshxona", "recipe", 0.7,
                      ["kuzgi_taom", "qovoq", "osh"], "Kuzning eng mazali taomlari"),
    ],
    11: [
        TrendingTopic("Uy qurilishi/ta'mirlash", "lifestyle", 0.6,
                      ["uy_tamiri", "dizayn", "interyer"], "Qishga tayyorgarlik"),
    ],
    12: [
        TrendingTopic("Yil yakunlari", "motivational", 0.85,
                      ["yil_yakuni", "natijalar", "minnatdorchilik"], "2026-yil natijalari"),
        TrendingTopic("Yangi yil tayyorgarligi", "lifestyle", 0.9,
                      ["yangi_yil", "sovgalar", "bayram"], "Eng yaxshi yangi yil sovg'alari"),
    ],
}


class TrendEngine:
    """Discovers trending topics for content planning."""

    @classmethod
    def get_current_trends(cls, limit: int = 5) -> list[TrendingTopic]:
        """Get currently relevant trending topics."""
        today = date.today()
        month = today.month
        trends = []

        # Monthly trends
        for trend in MONTHLY_TRENDS.get(month, []):
            trends.append(trend)

        # Calendar events (check within event window)
        for event in UZBEK_CALENDAR_EVENTS:
            event_date = cls._parse_event_date(event["date"], today.year)
            duration = event.get("duration", 1)
            window_start = event_date - __import__("datetime").timedelta(days=3)
            window_end = event_date + __import__("datetime").timedelta(days=duration)

            if window_start <= today <= window_end:
                # Boost relevance if we're in the window
                days_to_event = (event_date - today).days
                relevance = 0.95 if days_to_event >= 0 else max(0.5, 0.95 - (abs(days_to_event) * 0.1))

                trends.append(TrendingTopic(
                    name=event["name"],
                    category=event["category"],
                    relevance_score=relevance,
                    hashtags=event["hashtags"],
                    suggested_hook=f"{event['name']} muborak!",
                    source="calendar",
                    expires=window_end.isoformat(),
                ))

        # Sort by relevance
        trends.sort(key=lambda t: t.relevance_score, reverse=True)
        return trends[:limit]

    @classmethod
    def get_trending_hashtags(cls, category: str = "") -> list[str]:
        """Get trending hashtags, optionally filtered by category."""
        trends = cls.get_current_trends(limit=10)
        hashtags = []

        for trend in trends:
            if not category or trend.category == category:
                hashtags.extend(trend.hashtags)

        # Add evergreen Uzbek Instagram hashtags
        evergreen = [
            "uzbekistan", "tashkent", "uzbek", "uzbekcha",
            "hayot", "motivatsiya", "bilim", "rivojlanish",
        ]
        hashtags.extend(evergreen)

        return list(dict.fromkeys(hashtags))  # Dedupe preserving order

    @classmethod
    def suggest_content_for_trend(
        cls,
        trend: TrendingTopic,
    ) -> dict:
        """Suggest content parameters for a trending topic."""
        content_type_map = {
            "recipe": "reel",
            "travel": "carousel",
            "motivational": "reel",
            "educational": "carousel",
            "lifestyle": "image",
            "fashion": "carousel",
            "product": "reel",
        }

        return {
            "topic": trend.name,
            "category": trend.category,
            "content_type": content_type_map.get(trend.category, "reel"),
            "hashtags": trend.hashtags,
            "hook": trend.suggested_hook,
            "priority": max(1, int(trend.relevance_score * 10)),
        }

    @classmethod
    def display_trends(cls) -> str:
        """Display current trends as formatted text."""
        trends = cls.get_current_trends(limit=10)
        today = date.today()

        lines = [
            "=" * 65,
            f"  Trending Topics — {today.strftime('%B %d, %Y')}",
            "=" * 65,
        ]

        if not trends:
            lines.append("  No notable trends right now.")
        else:
            for i, trend in enumerate(trends, 1):
                lines.append(
                    f"  {i}. [{trend.relevance_score:.0%}] {trend.name} "
                    f"({trend.category})"
                )
                tags = " ".join(f"#{t}" for t in trend.hashtags[:5])
                lines.append(f"     Tags: {tags}")
                if trend.suggested_hook:
                    lines.append(f"     Hook: {trend.suggested_hook}")

        lines.append(f"\n{'=' * 65}")
        return "\n".join(lines)

    @staticmethod
    def _parse_event_date(date_str: str, year: int) -> date:
        month, day = date_str.split("-")
        return date(year, int(month), int(day))
