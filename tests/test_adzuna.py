from __future__ import annotations

from unittest.mock import patch

from scraper.adzuna import run_adzuna_scraper_sync
from scraper.config import ScraperConfig


MOCK_RESPONSE = {
    "results": [
        {
            "id": "123",
            "title": "Mechatronics Engineer Graduate",
            "company": {"display_name": "RoboCo"},
            "location": {"display_name": "Budapest"},
            "description": "Robotics and automation engineering role",
            "redirect_url": "https://example.com/jobs/123",
            "created": "2026-01-10T12:00:00Z",
        }
    ]
}


@patch("scraper.adzuna.save_scraped_jobs", return_value=1)
@patch("scraper.adzuna.notify_scrape_complete")
@patch("scraper.adzuna.send_telegram_message")
@patch("scraper.adzuna.httpx.get")
def test_adzuna_scraper_maps_results(mock_get, _tg, _notify, mock_save):
    mock_get.return_value.json.return_value = MOCK_RESPONSE
    mock_get.return_value.raise_for_status = lambda: None

    cfg = ScraperConfig.from_env()
    with patch.dict(
        "os.environ",
        {
            "ADZUNA_APP_ID": "test-app",
            "ADZUNA_APP_KEY": "test-key",
            "ADZUNA_COUNTRY_OFFSET": "0",
        },
        clear=False,
    ):
        result = run_adzuna_scraper_sync(cfg, country_batch_size=1)

    assert result["inserted"] == 1
    assert mock_save.called
    saved_jobs = mock_save.call_args[0][0]
    assert saved_jobs[0].source == "adzuna"
    assert saved_jobs[0].metadata["adzuna_id"] == "123"


@patch("scraper.adzuna.adzuna_configured", return_value=False)
def test_adzuna_skips_without_credentials(_configured):
    cfg = ScraperConfig.from_env()
    result = run_adzuna_scraper_sync(cfg)
    assert result["inserted"] == 0
    assert "skipped" in result["message"].lower()
