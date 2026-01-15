# 数据存储管理与外接硬盘配置指南

随着转录媒体数量的增加，本地磁盘空间可能会逐渐不足。本指南说明了如何管理数据文件夹，并将它们迁移/映射到外接硬盘。

---

## 1. 核心文件夹说明 (backend/)

在 `backend` 目录下，主要有三个文件夹占用空间：

*   **`downloads/` (最占空间)**: 存储下载的 YouTube 音频和上传的视频/音频原文件。
*   **`results/`**: 存储最终生成的转录 JSON 报告、状态文件和缩略图。
*   **`cache/`**: 存储 Whisper 转录的原始数据，用于加速重复访问。

---

## 2. 迁移至外接硬盘 (推荐方案：符号链接)

最简单且不破坏代码逻辑的方法是使用 **符号链接 (Symbolic Link)**。

### 操作步骤：

#### 第一步：停止服务
确保后端程序（Uvicorn）已完全关闭。

#### 第二步：准备外接硬盘目录
假设您的外接硬盘挂载路径为 `/Volumes/ExtremeSSD`，在其中创建一个项目专用文件夹：
```bash
mkdir -p /Volumes/ExtremeSSD/tldw_data
```

#### 第三步：迁移现有数据
将现有的数据文件夹移动到硬盘上（以 `downloads` 为例）：
```bash
mv backend/downloads /Volumes/ExtremeSSD/tldw_data/
```
*(对 `results` 和 `cache` 也可以执行同样的操作)*

#### 第四步：创建映射（软链接）
返回项目的 `backend` 目录，创建指向硬盘的链接：
```bash
ln -s /Volumes/ExtremeSSD/tldw_data/downloads ./downloads
```

---

## 3. 自动化清理建议

如果您不想使用外接硬盘，也可以定期运行维护脚本来释放空间：

```bash
cd backend
python maintenance.py
```

该脚本会自动：
1.  删除超过 1 小时且未被引用的原始媒体文件 (`downloads/`)。
2.  清理过期的任务状态记录。

---

## 4. 常见问题 (FAQ)

*   **链接失效怎么办？**：如果外接硬盘未挂载，后端启动时会报错或无法读取媒体。请确保在启动服务前硬盘已正确连接。
*   **权限问题**：部分移动硬盘（如 NTFS 格式在 Mac 下）可能存在写入权限问题。建议将硬盘格式化为 **APFS (Mac)** 或 **exFAT (通用)**。

---
*版本：v1.0 | 更新日期：2026-01-15*
