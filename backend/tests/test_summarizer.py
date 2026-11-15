import pytest
from app.services.summarizer import SummarizerService


@pytest.mark.asyncio
async def test_summarizer_with_gemini():
    title = "India Approves Historic Space Station Mission with $2.5B Funding"
    text = (
        "The Union Cabinet on Friday approved the initial phase of the Bharatiya Antariksh Station (BAS), "
        "allocating 21,000 crore rupees ($2.5 billion) toward module development and astronaut training. "
        "The first module, BAS-1, is scheduled for launch by 2028, establishing permanent Indian human presence "
        "in low Earth orbit. Prime Minister Modi termed the milestone a giant leap for indigenous science."
    )

    summary = await SummarizerService.summarize_article(title=title, text=text)
    assert summary is not None
    lines = [line.strip() for line in summary.split("\n") if line.strip()]

    # Assert exactly 3 bullet points
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("• ")

    # Assert under 65 words total
    word_count = len(summary.split())
    assert word_count <= 65
    print(f"\n[Generated Summary ({word_count} words)]:\n{summary}")


@pytest.mark.asyncio
async def test_summarizer_fallback():
    title = "Local Council Announces Weekend Road Closures for Marathon"
    text = (
        "Several central arterial roads will be temporarily closed from 6 AM to 1 PM this Sunday "
        "for the annual city marathon. Commuters are advised to take alternate metro routes."
    )

    fallback = SummarizerService._fallback_summary(title=title, text=text)
    assert fallback is not None
    lines = [line.strip() for line in fallback.split("\n") if line.strip()]
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("• ")
