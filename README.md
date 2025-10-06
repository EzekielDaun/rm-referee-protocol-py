# RM-referee-protocol-py

[RM-referee-protocol](https://github.com/EzekielDaun/rm-referee-protocol) 的 Python 包装，基于 PyO3。用于在 Python 中解析、查看、修改并构造裁判系统帧。

## 特性

- 从字节解析为 `RefereeFramePy`
- 读取/修改 `header.seq` 等头部字段
- 以 Python `dict`/`list` 读写 `cmd_data`（`cmd_data_py()` / `set_cmd_data_py()`）
- 构造：`RefereeFramePy.from_cmd_py(seq, dict)`
- 调用 `to_bytes()` 序列化回字节（自动更新 CRC）

## 安装

- 开发环境推荐：`pip install maturin && maturin develop`
- 或从 GitHub Releases 下载 wheel：`pip install <wheel.whl>`

## 示例

参考仓库中的 `examples.py` 与 `tests/test_protocol.py`。Python dict 字段名以 [Rust 版本](https://github.com/EzekielDaun/rm-referee-protocol)为准。
