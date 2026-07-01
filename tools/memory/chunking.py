import re


def chunk_markdown(text: str, path: str) -> list[dict]:
    """
    Split markdown text into chunks by heading level.

    Each chunk has the nearest preceding heading (or empty string if before any heading)
    and accumulates text until the next heading. Empty chunks are skipped.

    Args:
        text: Markdown text to chunk
        path: File path to include in each chunk record

    Returns:
        List of dicts with keys: path, heading, text
    """
    lines = text.split('\n')
    chunks = []
    current_heading = ""
    current_text = []

    for line in lines:
        # Check if this line is a heading (1-3 hashes followed by space)
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)

        if heading_match:
            # Save previous chunk if it has content
            if current_text:
                text_content = '\n'.join(current_text).strip()
                if text_content:  # Skip empty chunks
                    chunks.append({
                        'path': path,
                        'heading': current_heading,
                        'text': text_content
                    })

            # Start new chunk with this heading
            current_heading = heading_match.group(2).strip()
            current_text = []
        else:
            # Accumulate text under current heading
            current_text.append(line)

    # Don't forget the last chunk
    if current_text:
        text_content = '\n'.join(current_text).strip()
        if text_content:  # Skip empty chunks
            chunks.append({
                'path': path,
                'heading': current_heading,
                'text': text_content
            })

    return chunks
