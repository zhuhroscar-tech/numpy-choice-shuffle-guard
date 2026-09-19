# numpy-choice-shuffle-guard

[![English](https://img.shields.io/badge/English-555555?style=flat)](README.md) [![简体中文](https://img.shields.io/badge/%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-555555?style=flat)](README.zh-CN.md)

检测并规避一个真实存在、目前仍未修复的 numpy 缺陷：
[numpy/numpy#31210](https://github.com/numpy/numpy/issues/31210) ——
`numpy.random.Generator.choice(a, size, replace=False, p=<权重>)`
会**静默忽略 `shuffle` 参数**。当给定 `p` 且 `replace=False` 时，
`shuffle=True`（numpy 的默认值）与 `shuffle=False` 产生完全相同的输出。

## 为什么这很重要

如果你的代码在不放回抽样加权子集时依赖 `shuffle=True` 来随机化结果的
**抽取顺序**（例如流式/在线训练循环，或对顺序敏感的验证集划分），
结果的顺序会悄悄地与输入顺序相关，而不是真正被随机化——且不会有任何
报错或警告，被选中的**集合**本身也完全正确。只有**顺序**是错的，这使
得这类问题很容易在代码审查和只检查"选中的项目是否正确"而不检查
"顺序是否每次运行都真正随机"的单元测试中被忽略。

未加权的情况（`p=None`）**不受影响**——`shuffle` 在那条路径上工作正常。
本工具自身的探测逻辑刻意同时检查这两条路径，并且除非控制组（未加权）
也表现正确，否则绝不会报告"未受影响"，因此一个失效的探测逻辑绝不会
被误判为"缺陷已修复"（参见 [core.py](src/numpy_choice_shuffle_guard/core.py)
中 `detect_shuffle_ignored_bug` 的失效保护分支）。

## 提供的功能

- `detect_shuffle_ignored_bug()` / `numpy-choice-shuffle-guard detect`：
  对**已安装的** numpy 进行实时探测（绝不依赖版本号白名单，因为 numpy
  尚未宣布修复版本），报告该缺陷此刻是否可复现。
- `safe_weighted_choice()`：`Generator.choice` 的直接替代包装函数，
  会执行 numpy 自身调用悄悄跳过的洗牌步骤，并使用同一个 `rng`，
  因此抽样结果依然可以从调用者的 rng 状态完全复现。其他所有调用形式
  （`replace=True` 或 `p=None`）会原样透传给 numpy，不做任何修改。
- `independent_reference_weighted_sample_without_replacement()`：一个
  **独立的参照实现**（Efraimidis-Spirakis 指数键加权抽样——与 numpy
  自身的累积分布搜索是完全不同的算法），供
  `numpy-choice-shuffle-guard verify` 用来确认该规避方案在修正抽取顺序
  的同时，不会悄悄地改变**哪些**项目被选中的概率。

这是针对上游 numpy 缺陷的**规避方案，而非对 numpy 的补丁**，也不是在
说 numpy 本身不该使用——它的存在仅仅是为了在 numpy/numpy#31210
被上游修复之前提供保护。

## 安装与运行

需要 Python 3.9+ 和 numpy>=1.24。无 GPU 需求，无编译扩展。

```bash
git clone https://github.com/zhuhroscar-tech/numpy-choice-shuffle-guard.git
cd numpy-choice-shuffle-guard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

```bash
numpy-choice-shuffle-guard detect            # 探测已安装的 numpy
numpy-choice-shuffle-guard detect --json
numpy-choice-shuffle-guard verify            # 与独立参照实现进行统计校验
numpy-choice-shuffle-guard --no-color detect
```

`detect` 在确认缺陷存在时（或探测本身不确定时——出于安全考虑）退出码
为 `1`，未复现时为 `0`。`verify` 在 `safe_weighted_choice` 的选择频率
与独立参照实现的偏差超过 `--tolerance`（默认 `0.05`）时退出码为 `1`。

## 验证记录

- 在编写本工具之前，已在本项目锁定的 numpy 版本（2.5.2）上独立复现：
  `Generator.choice(replace=False, p=权重, shuffle=True)` 与
  `shuffle=False` 产生完全相同的输出；未加权的控制组则正确地表现出
  差异。详见上游 issue 中的原始报告及对 `_generator.pyx` 的根因追溯。
- 中/日文披露：在候选评估阶段，中文和日文查询均未发现关于此具体缺陷
  的母语社区讨论——仅找到英文来源（GitHub issue 本身及 numpy 官方文档）。
  在此如实披露，而非暗示存在广泛的社区需求；本工具的存在是因为该缺陷
  真实且可独立复现，而非因为任一语言社区的强烈需求。
- CI 在 `ubuntu-latest` 和 `macos-latest` 上运行完整测试套件
  （包括针对 CI 运行器自身已安装 numpy 的真实、未打桩的复现测试），
  并附带 wheel/sdist 构建与冒烟测试任务及校验和发布产物。

## 局限性

- 本工具仅检测并规避 numpy/numpy#31210 所述的 `replace=False` +
  `p is not None` 组合，不审计 numpy 随机数 API 的其他任何正确性问题。
- `detect` 的实时探测默认使用较小的固定种群/样本规模；它是功能性复现，
  而非针对所有种群规模或 numpy 构建版本的统计证明。
- 如果 numpy 上游修复了此问题，`safe_weighted_choice` 会自动检测到并
  停止应用手动洗牌——但这并不能替代在你的最低支持 numpy 版本已包含
  修复后最终移除该规避方案。

## 开发与卸载

```bash
python -m pytest -q --cov=numpy_choice_shuffle_guard --cov-report=term-missing
python -m pip uninstall numpy-choice-shuffle-guard
```

[Releases](https://github.com/zhuhroscar-tech/numpy-choice-shuffle-guard/releases) · [MIT 许可证](LICENSE)
