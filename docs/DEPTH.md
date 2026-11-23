# 分段计时席业务与测试登记

- 规模：中型
- 使用者：路跑赛事计时裁判
- 核心规则：从乱序读数中寻找完整合法的计时点组合，按总时长与分段时间排序，避免局部最早读数封死后续。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 芯片读数 | 检查编码、字段宽度和来源行 | `POST /api/intake` | `app/modules/intake/service.py` | `tests/test_intake.py` |
| M2 计时点约定 | 归一修订、业务键和偏移时间 | `POST /api/contract` | `app/modules/contract/service.py` | `tests/test_contract.py` |
| M3 异常计时卡 | 定位重复、被替代与矛盾来源 | `POST /api/quality` | `app/modules/quality/versions.py` | `tests/test_quality.py` |
| M4 分段择链 | 按规则复算并追溯证据 | `POST /api/domain` | `app/modules/domain/rule.py` | `tests/test_domain.py` |
| M5 成绩核对 | 核对独立清单和各类差异 | `POST /api/reconcile` | `app/modules/reconcile/service.py` | `tests/test_reconcile.py` |
| M6 计时批次 | 打开历史批次并对原文件复跑 | `POST /api/runs` | `app/modules/runs/service.py` | `tests/test_runs.py` |
| M7 裁判签核 | 登记复核结论并下载证据 | `POST /api/review/{run_id}` | `app/modules/review/decisions.py` | `tests/test_review.py` |

## 陷阱登记

| TRAP | 现象 | 样例 | 处理位置 | 测试 |
|---|---|---|---|---|
| TRAP-01 | GB18030 来源文件 | legacy.csv | `app/modules/intake/reader.py` | `tests/test_intake.py::test_gb18030` |
| TRAP-02 | BOM 前缀 | shift.csv | `app/modules/intake/reader.py` | `tests/test_intake.py::test_bom` |
| TRAP-03 | 备注含引号内换行 | shift.csv | `app/modules/intake/service.py` | `tests/test_intake.py::test_multiline` |
| TRAP-04 | 分段重复表头 | shift.csv | `app/modules/intake/service.py` | `tests/test_intake.py::test_repeated` |
| TRAP-05 | 列数不足 | shift.csv | `app/modules/intake/service.py` | `tests/test_intake.py::test_width` |
| TRAP-07 | 缺测哨兵 | shift.csv | `app/modules/contract/service.py` | `tests/test_contract.py::test_missing` |
| TRAP-08 | 前导零的单号 | shift.csv | `app/modules/contract/service.py` | `tests/test_contract.py::test_leading_zero` |
| TRAP-11 | 偏移时刻 UTC 归一 | shift.csv | `app/modules/domain/values.py` | `tests/test_contract.py::test_offsets` |
| TRAP-14 | 同版业务字段冲突 | shift.csv | `app/modules/quality/versions.py` | `tests/test_quality.py::test_conflicting` |
| TRAP-16 | 末行引号截断 | truncated.csv | `app/modules/intake/reader.py` | `tests/test_intake.py::test_truncated_rejected` |
| TRAP-17 | 旧版列名映射 | legacy.csv | `app/modules/contract/schema.py` | `tests/test_contract.py::test_legacy_aliased` |
| TRAP-18 | 空文件、空白文件与仅表头 | 测试构造 | `app/modules/intake/service.py` | `tests/test_intake.py::test_empty_states` |
| TRAP-26 | 陈旧复核版本拒绝 | 测试构造 | `app/modules/review/decisions.py` | `tests/test_review.py::test_stale` |
| TRAP-13 | backtrack | cases.csv | `app/modules/domain/rule.py` | `tests/test_domain.py::test_backtrack` |
| TRAP-19 | same finish | cases.csv | `app/modules/domain/rule.py` | `tests/test_domain.py::test_same_finish` |

## 对账

输入 = 计入 + 隔离 + 重传及版本替换 + 空白记录 + 重复表头。按业务键全外连接，缺失一侧与数值为零分别登记。逐笔差值与总差一致。
