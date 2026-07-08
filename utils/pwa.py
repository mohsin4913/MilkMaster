from pathlib import Path


def collect_static_asset_urls(static_folder):
    static_path = Path(static_folder)
    asset_urls = []

    for file_path in static_path.rglob("*"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(static_path).as_posix()
        asset_urls.append(f"/static/{relative_path}")

    asset_urls.sort()
    return asset_urls
