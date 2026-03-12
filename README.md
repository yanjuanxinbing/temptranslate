# Ren'Py Real-time Translator

本文件为AI生成，目前机器翻译最为简单通用，AI模式需要自行部署。

一个用于实时翻译 Ren'Py 游戏对话的工具，支持机器翻译和 AI 翻译两种模式。

## 功能特点

- 🎮 **实时监听**：通过内存读取实时获取 Ren'Py 游戏中的对话文本
- 🤖 **双翻译模式**：
  - 机器翻译：基于百度翻译 API
  - AI 翻译：基于 Ollama 本地大语言模型（translategemma:4b）
- 💾 **智能缓存**：LRU 缓存机制，避免重复翻译
- 🎨 **现代界面**：基于 CustomTkinter 的现代化 GUI
- ⚡ **高性能**：异步处理，响应迅速

## 系统要求

- Python 3.8+
- Windows 操作系统（使用 pymem 进行内存读取）
- Ollama（如果使用 AI 翻译模式）

## 安装依赖

```bash
pip install customtkinter pymem aiohttp ollama
```

## AI 翻译模式配置

如果要使用 AI 翻译模式，需要先安装 Ollama 并下载模型：

1. 下载安装 [Ollama](https://ollama.ai/)
2. 拉取翻译模型：
```bash
ollama pull translategemma:4b
```

## 使用方法

1. 启动目标 Ren'Py 游戏（默认进程名：`LessonsInLove`）
2. 运行翻译工具：
```bash
python main.py
```
3. 点击"开始"按钮开始翻译
4. 点击"AI模式"/"机器翻译"按钮切换翻译模式

## 项目结构

```
.
├── main.py          # 主程序入口，GUI 界面
├── translator.py    # 翻译器实现（机器翻译和 AI 翻译）
├── listener.py      # Ren'Py 内存监听器
└── cache.py         # LRU 缓存实现
```

## 核心模块说明

### main.py
- 使用 CustomTkinter 构建 GUI
- 管理翻译线程的启动/暂停
- 支持运行时切换翻译模式

### translator.py
- `Translator`：机器翻译类，使用百度翻译 API
- `AiTranslator`：AI 翻译类，使用 Ollama 本地模型
- 异步处理翻译请求，提高响应速度

### listener.py
- `RenpyMemoryListener`：内存监听器
- 通过 pymem 读取游戏进程内存
- 解析 Python 内部数据结构（PyUnicode、PyDict）
- 自动过滤 Ren'Py 标签（如 `{tag}`）

### cache.py
- `LRU`：最近最少使用缓存
- 容量默认 128 条
- 使用双向链表实现，O(1) 时间复杂度

## 技术细节

### 内存读取原理
1. 扫描进程内存查找 `renpy.store` 字符串
2. 定位 `renpy.store.__dict__` 对象
3. 查找 `_last_say_what` 变量
4. 解析 PyUnicode 对象获取对话文本

### PyUnicode 解析
支持三种 Unicode 编码格式：
- KIND_1BYTE：Latin-1（ASCII）
- KIND_2BYTE：UTF-16-LE
- KIND_4BYTE：UTF-32

### 翻译流程
1. 监听器检测到新对话文本
2. 查询 LRU 缓存
3. 缓存未命中时调用翻译 API/模型
4. 更新缓存并显示翻译结果

## 自定义配置

### 修改目标进程
编辑 `translator.py` 中的进程名：
```python
self.listener = RenpyMemoryListener("YourGameProcessName")
```

### 修改 AI 模型
编辑 `translator.py` 中的模型配置：
```python
self.model = "your-model-name"
```

### 调整缓存大小
编辑 `translator.py` 中的缓存容量：
```python
self.cache = LRU(256)  # 默认 128
```

## 注意事项

- ⚠️ 本工具仅用于学习和个人使用
- ⚠️ 需要游戏进程具有可读内存权限
- ⚠️ 不同版本的 Python 解释器内存结构可能不同
- ⚠️ 机器翻译模式依赖百度翻译接口的可用性
- ⚠️ AI 翻译模式需要本地运行 Ollama 服务

## 常见问题

**Q: 提示"无法找到 renpy.store.__dict__"**  
A: 确保游戏进程名正确，并且游戏已完全启动

**Q: AI 翻译没有响应**  
A: 检查 Ollama 服务是否运行，模型是否已下载

**Q: 翻译质量不佳**  
A: 可以尝试调整 AI 模型的 system prompt 或使用其他翻译模型

## 许可证

本项目仅供学习交流使用。

## 贡献

欢迎提交 Issue 和 Pull Request！
