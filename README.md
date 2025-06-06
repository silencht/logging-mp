# logging-mp

> 🧰 一个支持多进程、带有 Rich 彩色输出的日志系统（multiprocessing-safe logging system with Rich support）

`logging-mp` 是一个轻量级的 Python 日志工具，解决了在多进程环境下日志错乱、丢失、顺序混乱等问题，并支持漂亮的终端输出（基于 [`rich`](https://github.com/Textualize/rich)）。

---

## 🚀 特性 Features

- ✅ **多进程安全**：使用 `multiprocessing.Queue` 和 `QueueHandler` 实现
- ✅ **独立日志监听进程**：避免主进程阻塞
- ✅ **彩色终端输出**：集成 `rich.logging.RichHandler`
- ✅ **支持动态日志等级设置**：兼容 `logging.DEBUG/INFO/WARNING/...`
- ✅ **简单易用**：无需复杂配置，一行代码启动

---

## 📦 安装 Installation

```bash
pip install logging-mp
```
或克隆本仓库:
```bash
git clone https://github.com/silencht/logging-mp.git
cd logging-mp
pip install .
```

## 🛠️ 使用方法 Usage

查看 `test_log_tool_mp.py`

## 📄 License
本项目采用 MIT License。

