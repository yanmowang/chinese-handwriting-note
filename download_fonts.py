import requests
import os

fonts = {
    "MaShanZheng-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/mashanzheng/MaShanZheng-Regular.ttf",
    "LongCang-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/longcang/LongCang-Regular.ttf",
    "ZhiMangXing-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/zhimangxing/ZhiMangXing-Regular.ttf"
}

output_dir = "fonts"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for name, url in fonts.items():
    print(f"Downloading {name}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(os.path.join(output_dir, name), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
