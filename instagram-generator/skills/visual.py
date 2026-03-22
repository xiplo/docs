"""Visual composition skills — reusable visual intelligence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisualComposition:
    layout: str
    focal_points: list[str]
    depth_layers: list[str]
    color_harmony: str
    aspect_ratio: str


class VisualSkills:
    """Skills for visual composition and style decisions."""

    @staticmethod
    def compose_rule_of_thirds(
        subject: str, background: str, aspect_ratio: str = "9:16"
    ) -> VisualComposition:
        """Apply rule of thirds composition."""
        return VisualComposition(
            layout="rule_of_thirds",
            focal_points=[
                f"top-left intersection: sky/environment",
                f"center-right intersection: {subject}",
                f"bottom-left: {background} leading line",
            ],
            depth_layers=[
                f"foreground: close detail element",
                f"midground: {subject}",
                f"background: {background}",
            ],
            color_harmony="complementary",
            aspect_ratio=aspect_ratio,
        )

    @staticmethod
    def compose_centered(
        subject: str, aspect_ratio: str = "1:1"
    ) -> VisualComposition:
        """Create a centered, symmetrical composition."""
        return VisualComposition(
            layout="centered_symmetrical",
            focal_points=[f"dead center: {subject}"],
            depth_layers=[
                f"foreground: vignette/frame",
                f"center: {subject} sharp focus",
                f"background: soft bokeh",
            ],
            color_harmony="monochromatic",
            aspect_ratio=aspect_ratio,
        )

    @staticmethod
    def compose_dynamic_diagonal(
        subject: str, motion_direction: str = "left_to_right"
    ) -> VisualComposition:
        """Create dynamic diagonal composition for action/energy."""
        return VisualComposition(
            layout="dynamic_diagonal",
            focal_points=[
                f"diagonal line from bottom-left to top-right",
                f"subject {subject} along diagonal",
            ],
            depth_layers=[
                f"foreground: motion blur element",
                f"midground: {subject} in motion",
                f"background: contrasting environment",
            ],
            color_harmony="split_complementary",
            aspect_ratio="9:16",
        )

    @staticmethod
    def get_aspect_prompt(aspect_ratio: str) -> str:
        """Get composition instructions for specific aspect ratios."""
        guides = {
            "9:16": (
                "vertical composition optimized for mobile viewing, "
                "subject in center-third, leave top 15% for safe zone, "
                "bottom 20% for text overlay area"
            ),
            "4:5": (
                "portrait orientation, subject fills 60% of frame, "
                "leave bottom margin for caption preview"
            ),
            "1:1": (
                "square composition, balanced visual weight, "
                "strong central focal point"
            ),
            "16:9": (
                "cinematic widescreen, horizontal emphasis, "
                "use leading lines from edges to center"
            ),
        }
        return guides.get(aspect_ratio, guides["9:16"])

    @staticmethod
    def suggest_color_harmony(
        base_color: str, mood: str
    ) -> dict[str, str]:
        """Suggest harmonious colors based on a base color and mood."""
        harmonies = {
            "warm": {
                "primary": base_color,
                "secondary": "golden amber",
                "accent": "burnt sienna",
                "neutral": "cream white",
                "shadow": "deep brown",
            },
            "cool": {
                "primary": base_color,
                "secondary": "steel blue",
                "accent": "teal",
                "neutral": "light gray",
                "shadow": "navy",
            },
            "vibrant": {
                "primary": base_color,
                "secondary": "coral",
                "accent": "electric blue",
                "neutral": "off-white",
                "shadow": "charcoal",
            },
            "moody": {
                "primary": base_color,
                "secondary": "deep purple",
                "accent": "gold",
                "neutral": "dark gray",
                "shadow": "near black",
            },
        }
        return harmonies.get(mood, harmonies["warm"])

    @staticmethod
    def build_lighting_prompt(
        setup: str,
        time_of_day: str = "golden_hour",
        intensity: str = "medium",
    ) -> str:
        """Build a detailed lighting description for image generation."""
        setups = {
            "three_point": (
                f"three-point lighting setup, key light from 45 degrees, "
                f"fill light opposite side at half intensity, "
                f"rim light from behind for subject separation"
            ),
            "natural": (
                f"natural {time_of_day} lighting, "
                f"soft diffused sunlight, natural shadows"
            ),
            "dramatic": (
                f"dramatic single-source lighting, deep shadows, "
                f"high contrast, chiaroscuro effect"
            ),
            "flat": (
                f"flat even lighting, minimal shadows, "
                f"soft diffused light from multiple sources"
            ),
            "rembrandt": (
                f"Rembrandt lighting, triangle of light on shadow side of face, "
                f"classic portrait lighting setup"
            ),
            "neon": (
                f"neon glow lighting, colored light sources, "
                f"cyan and magenta accent lights, dark environment"
            ),
        }
        base = setups.get(setup, setups["natural"])

        intensities = {
            "low": "subtle, understated lighting",
            "medium": "balanced, natural-feeling light",
            "high": "intense, vivid lighting with strong highlights",
        }
        return f"{base}, {intensities.get(intensity, intensities['medium'])}"
