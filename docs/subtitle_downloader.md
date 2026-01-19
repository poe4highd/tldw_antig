# YouTube 字幕下载工具

该脚本用于快速下载 YouTube 视频的字幕，并将其保存到测试数据目录中，以便进行转录校对或其他测试。

## 放置路径
脚本：`backend/scripts/download_subs.py`
数据目录：`backend/tests/data/`

## 依赖要求
- Python 3.x
- `yt-dlp`: 请确保已安装并可在路径中直接调用。
  ```bash
  pip install yt-dlp
  ```

## 使用方法

### 1. 使用视频 ID 下载
```bash
python3 backend/scripts/download_subs.py dQw4w9WgXcQ
```

### 2. 使用视频 URL 下载
```bash
python3 backend/scripts/download_subs.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### 3. 指定输出目录
```bash
python3 backend/scripts/download_subs.py dQw4w9WgXcQ --outdir ./mylab
```

## 功能说明
- **跳过视频下载**：仅下载字幕元数据，节省带宽。
- **自动尝试多种语言**：默认尝试顺序为 `zh-Hans` (简体中文), `zh` (通用中文), `en` (英文)。
- **包含自动生成字幕**：如果视频没有提供人工上传的字幕，脚本会尝试获取 YouTube 自动生成的字幕。
- **多格式支持**：优先下载 `srv1`, `vtt` 或 `ttml` 格式。

## 开发者说明
该脚本主要用于收集真实视频的字幕作为测试用例，配合 `backend/tests/` 下的其他测试脚本使用。
