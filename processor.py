import claude_client


async def process(text: str, images: list) -> dict:
    """Orchestrate Claude generation from extracted text and images."""
    if not text.strip() and not images:
        raise ValueError("No content extracted from the provided input.")
    return await claude_client.generate_all(text, images)
