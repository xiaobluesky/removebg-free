# 🎨 Remove.bg Free

**开源免费的背景移除工具 · 完全替代 Remove.bg**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ 特性

- ✅ **完全免费** - 无任何收费限制
- ✅ **开源透明** - 代码完全公开，可审计
- ✅ **无使用限制** - 无次数限制，无分辨率限制
- ✅ **本地部署** - 数据不出本地，隐私安全
- ✅ **高质量** - 基于 U²-Net 模型，效果优秀

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/removebg-free.git
cd removebg-free

# 启动服务
docker-compose up -d

# 访问 http://localhost:3000
```

### 方式二：本地运行

#### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 前端

直接打开 `frontend/index.html` 或使用任意静态服务器：

```bash
cd frontend
python -m http.server 3000
```

---

## 📦 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + rembg (U²-Net) |
| 前端 | React + Tailwind CSS |
| 部署 | Docker + HuggingFace Spaces |
| 模型 | U²-Net (预训练) |

---

## 🔌 API 接口

### 单图处理

```bash
curl -X POST http://localhost:8000/api/remove-bg \
  -F "file=@image.png" \
  -o output.png
```

### 批量处理（最多 10 张）

```bash
curl -X POST http://localhost:8000/api/batch-remove-bg \
  -F "files=@image1.png" \
  -F "files=@image2.png" \
  -o results.json
```

### 健康检查

```bash
curl http://localhost:8000/health
```

---

## 📅 开发进度

| 阶段 | 功能 | 状态 |
|------|------|------|
| P0 | 拖拽上传 + 自动抠图 + 下载 PNG | ✅ 完成 |
| P1 | 批量处理（最多 10 张） | 🔄 开发中 |
| P2 | API 接口 | ✅ 完成 |

---

## 🎯 对比 Remove.bg

| 功能 | Remove.bg | Remove.bg Free |
|------|-----------|----------------|
| 免费额度 | 1 张/天 | 无限 |
| 高清下载 | 收费 | 免费 |
| 批量处理 | 收费 | 免费 |
| API 调用 | 收费 | 免费 |
| 本地部署 | ❌ | ✅ |
| 开源 | ❌ | ✅ |

---

## 📄 许可证

MIT License - 想怎么用就怎么用

---

## 🙏 致谢

- [rembg](https://github.com/danielgatis/rembg) - 背景移除库
- [U²-Net](https://github.com/xuebinqin/U-2-Net) - 模型架构
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

**Stars 是评分标准，不是变现手段** ⭐
