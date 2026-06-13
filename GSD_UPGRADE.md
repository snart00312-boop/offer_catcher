# Offer Catcher GSD Upgrade Brief

本文档给后续接管项目的自动化开发代理使用。当前环境没有可用的 `gsd` 命令，因此本轮没有初始化 `.gsd/` 状态目录，也没有运行 `gsd headless query`。项目已经具备可测试的安全配置、可解释匹配引擎、结果页推荐展示和部署说明，可作为 GSD 第一个里程碑的基线。

## 前置条件

1. 安装可用的 GSD CLI，并确认命令可执行。
2. 在项目根目录运行 GSD，不要从上级目录启动。
3. 启动前确认真实密钥只存在于本地环境或 Streamlit secrets 中，不进入版本控制。
4. 每个 slice 完成后必须运行测试，并做一次独立代码审阅。

## 建议里程碑

目标：把 Offer Catcher 从演示型原型升级为可解释、可测试、密钥安全的岗位匹配 MVP。

验收标准：

- AI 配置测试不会读取开发机真实 secrets。
- 没有 AI key 时仍能展示确定性的岗位推荐结果。
- 匹配结果包含综合分、推荐档、命中技能、关键缺口、学历状态、专业相关度、城市偏好。
- AI 只解释和延展确定性匹配结果，不替代排序来源。
- 全量 pytest 通过。
- 部署文档能让新开发者完成本地运行、AI 配置和测试验证。

## 推荐 Slices

### S01 安全配置与测试隔离

范围：AI 配置读取、错误脱敏、测试环境隔离。

验收：单测能在本地存在真实 secrets 的情况下稳定通过，并且失败输出不暴露 key。

### S02 可解释匹配引擎

范围：学历门槛解析、技能短语匹配、专业字段、目标岗位、城市偏好和分项解释。

验收：典型后端、数据分析、设计、运营画像都有稳定 Top N 排名测试。

### S03 结果页产品化

范围：推荐清单、首选岗位解释、技能缺口、AI 深入对话入口。

验收：不配置 AI key 也能完成从表单到推荐结果的主流程。

### S04 工程结构与部署说明

范围：拆分展示转换、配置文档、部署检查清单。

验收：文档冷启动可执行，测试和编译命令通过。

### S05 浏览器级验收

范围：启动 Streamlit，提交样例画像，验证推荐表和 AI 不可用提示。

验收：桌面和窄屏视口均无明显布局重叠，主流程截图可留档。

## 建议启动命令

安装 GSD 后，可用本文件作为新 milestone context：

```powershell
gsd headless --output-format json --context GSD_UPGRADE.md new-milestone --auto
```

如果需要逐步人工监督：

```powershell
gsd headless --output-format json --context GSD_UPGRADE.md new-milestone
gsd headless --output-format json next
```

## 当前基线验证

当前基线的最低验证命令：

```powershell
python -m pytest -q
python -m compileall app.py services data ui tests
```

