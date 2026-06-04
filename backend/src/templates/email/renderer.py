import os
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.core.logger import get_logger

logger = get_logger("templates:email")

TEMPLATE_DIR = Path(__file__).resolve().parent

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


class TemplateRenderError(Exception):
    """Raised when an email template cannot be rendered or compiled."""


def _render_compiled_template(template_name: str, context: dict) -> str | None:
    """Render a precompiled HTML template if present."""
    compiled_name = f"{template_name}.compiled.html"
    try:
        compiled_template = _env.get_template(compiled_name)
    except TemplateNotFound:
        return None

    return compiled_template.render(**context)


def _compile_mjml(mjml_markup: str) -> str | None:
    """
    Compile MJML into HTML using the configured binary.
    Returns HTML when successful, or None when compilation fails.
    """
    command = os.getenv("MJML_BINARY", "mjml")
    try:
        result = subprocess.run(
            [command, "-i", "-s"],
            input=mjml_markup.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except FileNotFoundError:
        logger.warning("MJML binary '%s' not found; using fallback HTML.", command)
        return None
    except subprocess.CalledProcessError as exc:  # noqa: PERF203
        stderr = (exc.stderr or b"").decode("utf-8", errors="ignore").strip()
        logger.error("MJML compilation failed: %s", stderr or exc)
        return None

    return result.stdout.decode("utf-8")


def render_email_template(template_name: str, context: dict, *, fallback_plain: str | None = None) -> str:
    """
    Render a precompiled HTML template when available. Falls back to compiling
    MJML at runtime (if the MJML binary exists) and finally to the lightweight
    HTML/plain-text fallbacks.
    """
    compiled = _render_compiled_template(template_name, context)
    if compiled:
        return compiled

    try:
        mjml_template = _env.get_template(f"{template_name}.mjml")
    except TemplateNotFound as exc:  # pragma: no cover - defensive
        raise TemplateRenderError(f"Template '{template_name}' not found") from exc

    mjml_markup = mjml_template.render(**context)
    html = _compile_mjml(mjml_markup)
    if html:
        return html

    # Fallback to a lightweight HTML template if MJML isn't available
    try:
        fallback_template = _env.get_template(f"{template_name}.fallback.html")
        logger.info("Using HTML fallback for email template '%s'.", template_name)
        return fallback_template.render(**context)
    except TemplateNotFound:
        pass

    if fallback_plain:
        logger.info("Using plain fallback body for email template '%s'.", template_name)
        return fallback_plain

    raise TemplateRenderError(f"Failed to render email template '{template_name}'")
