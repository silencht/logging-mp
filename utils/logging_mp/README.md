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
```python
from multiprocessing import Process
from logging_mp import logging_mp

def worker(name, level=None):
    # 如果没有设置 level，就使用全局默认等级
    logger = logging_mp.get_logger(name, level=level)

    logger.debug(f"[{name}] debug —— 调试细节")
    logger.info(f"[{name}] info —— 普通信息")
    logger.warning(f"[{name}] warning —— 警告但可以运行")
    logger.error(f"[{name}] error —— 出错但还能撑住")
    logger.critical(f"[{name}] critical —— 严重错误可能导致崩溃")

if __name__ == "__main__":
    # 全局默认等级：INFO（即不显示 debug）
    logging_mp.basic_config(level=logging_mp.INFO)

    main_logger = logging_mp.get_logger("main")
    main_logger.info("主进程启动")

    # 启动多个子进程：
    # 👉 worker-A：不设置等级，使用全局 INFO
    # 👉 worker-B：设置为 DEBUG，打印全部
    # 👉 worker-C：设置为 WARNING，只显示 warning 及以上
    # 👉 worker-D：不设置等级，也服从全局 INFO
    processes = [
        Process(target=worker, args=("worker-A",)),                        # 使用全局等级 INFO
        Process(target=worker, args=("worker-B", logging_mp.DEBUG)),       # 单独设置为 DEBUG
        Process(target=worker, args=("worker-C", logging_mp.WARNING)),     # 单独设置为 WARNING
        Process(target=worker, args=("worker-D",)),                        # 使用全局等级 INFO
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    main_logger.info("主进程结束")
```
## 📄 License
本项目采用 MIT License。

