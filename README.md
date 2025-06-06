## logging-mp
### 🧰 A multiprocessing-safe logging system with Rich colored output support

logging-mp is a lightweight Python logging tool designed to solve issues like log disorder, loss, and sequence confusion in multiprocessing environments. It also supports beautiful terminal output powered by rich.

### 🚀 Features
✅ Multiprocessing safe: implemented with multiprocessing.Queue and QueueHandler

✅ Dedicated log listener process: avoids blocking the main process

✅ Colored terminal output: integrated with rich.logging.RichHandler

✅ Supports dynamic log level setting: compatible with logging.DEBUG/INFO/WARNING/...

✅ Simple and easy to use: start with just one line of code, no complex configuration required

### 📦 Installation
```bash
pip install logging-mp
```

or clone this repository:

```bash
git clone https://github.com/silencht/logging-mp.git
cd logging-mp/utils/logging_mp
pip install -e .
```

### 🛠️ Usage
See test_log_tool_mp.py

### 📄 License
This project is licensed under the MIT License.