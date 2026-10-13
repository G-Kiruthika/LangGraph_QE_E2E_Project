import pytest
import os

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {
        **browser_type_launch_args,
        "headless": True,
        "args": ["--ignore-certificate-errors", "--no-sandbox"]
    }

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    videos_dir = os.path.join(os.getcwd(), "outputs", "reports", "videos")
    os.makedirs(videos_dir, exist_ok=True)
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "record_video_dir": videos_dir,
        "record_video_size": {"width": 1280, "height": 720}
    }
