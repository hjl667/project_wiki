from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from infographics_utils.constants import (
    IMAGE_WIDTH,
    INFOGRAPHICS_PATH,
    SECTION_01_PATH,
    SECTION_02_PATH,
    TERM_ILLUSTRATION_PATH,
)
from infographics_utils.make_quote_component import make_quote_block
from infographics_utils.make_text_block import (
    generate_text_from_news,
    make_text_block,
)
from infographics_utils.utils import (
    generate_term_explanation_component,
    get_color_clusters,
    get_prominent_colors,
)
from src.news_writer.reporter_repositor.utils import assign_reporter
from src.shared.constants.alembic import ALEMBIC_CONFIG_PATH
from src.shared.db_queries.listen2ai import fetch_recent_unique_articles
from src.shared.types.news import (
    Language,
    Listen2AICategory,
    PoliticalOrientation,
    Verbosity,
)
from src.shared.types.reporter import Reporter
from src.shared.utils import log
from src.shared.utils.db import create_session


def assemble_infographics(canvas_width, background_color, spacing=50):

    next_y_position = spacing
    text_block_01 = Image.open(SECTION_01_PATH)
    text_block_02 = Image.open(SECTION_02_PATH)

    canvas_height = 4 * spacing + text_block_01.height + text_block_02.height

    canvas = Image.new("RGB", (canvas_width, canvas_height), background_color)
    draw = ImageDraw.Draw(canvas)

    x = (canvas_width - text_block_01.width) // 2
    canvas.paste(text_block_01, (0, next_y_position))
    next_y_position += spacing + text_block_01.height

    x = (canvas_width - text_block_02.width) // 2
    canvas.paste(text_block_02, (0, next_y_position))
    next_y_position += spacing + text_block_02.height

    canvas.save(INFOGRAPHICS_PATH)
    log.info("Infographic generated and saved as 'infographics.png'")


def prepare_components(script_dict: dict):
    # generate the first term block
    term = generate_term_explanation_component(script_dict, False)
    color_clusters = get_color_clusters()

    # generate the first text_block
    main_colors = get_prominent_colors(TERM_ILLUSTRATION_PATH, 10)
    make_text_block(
        main_colors[0][0],
        color_clusters[1],
        "01",
        script_dict["01"]["subtitle"],
        script_dict["01"]["content"],
    )

    # generate the second term block and graph
    generate_term_explanation_component(script_dict, True, term)

    # generate the second text block
    make_quote_block(script_dict, main_colors, color_clusters)
    make_text_block(
        main_colors[0][0],
        color_clusters[1],
        "02",
        script_dict["02"]["subtitle"],
        script_dict["02"]["content"],
    )

    return main_colors


def make_infographics(news: dict, language, political_orientation, section_count=2):
    script = generate_text_from_news(news, language, political_orientation, section_count)
    colors = prepare_components(script)
    assemble_infographics(IMAGE_WIDTH, colors[0][0], 50)


def test_infographics():
    with create_session(
        alembic_config_path=ALEMBIC_CONFIG_PATH,
        pool_recycle=1200,
    ) as session:
        try:
            recently_published = fetch_recent_unique_articles(
                session,
                days=2,
                category=Listen2AICategory.GENERAL,
            ).all()
            if recently_published:
                news_dict = recently_published[0].article
                language = Language.ENGLISH
                political_orientation = PoliticalOrientation.NEUTRAL
                make_infographics(news_dict, language, political_orientation)
            else:
                log.error("No news articles found in the database.")
        except Exception as e:
            log.error(f"An error occurred: {e}")


def create_infographics(
    article: Dict,
    topic: str,
    language: Language,
    political_orientation: PoliticalOrientation,
    reporters: List[Reporter],
    length_limit: int = 0,
) -> Tuple[str, Sequence[Reporter], List]:
    make_infographics(article, language, political_orientation)
    return ("", reporters, [])


if __name__ == "__main__":
    test_infographics()