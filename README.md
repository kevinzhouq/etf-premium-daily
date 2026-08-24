# ETF 每日溢价率排行

每个交易日北京时间 09:45、14:30、16:30 获取 9 只跨境 ETF 的最新价和 IOPV，分别用于盘初观察、盘中决策参考和收盘归档；每次运行都会计算溢价率，生成中文排行榜、GitHub Pages 页面，并通过 Server酱发送到微信。

> 本项目仅做公开行情整理，不构成投资建议。溢价率并不等于未来收益，也不能单独作为交易依据。

## 监控基金

| 代码 | 展示名称 | 市场 |
|---|---|---|
| 159655 | 华夏标普500 | 深圳 |
| 159612 | 国泰标普500 | 深圳 |
| 159659 | 招商纳斯达克100 | 深圳 |
| 513870 | 富国纳斯达克100 | 上海 |
| 159696 | 易方达纳斯达克100 | 深圳 |
| 159501 | 嘉实纳斯达克100 | 深圳 |
| 159941 | 广发纳斯达克100 | 深圳 |
| 513110 | 华泰柏瑞纳斯达克100 | 上海 |
| 159509 | 景顺长城纳斯达克科技 | 深圳 |

基金池由 `config/funds.yaml` 管理。启动时会拒绝重复代码、非六位代码和 SH/SZ 之外的市场；任意一只启用基金缺失时，不会发布残缺的新榜单。

## 数据口径

行情来自 AkShare 的东方财富 ETF 实时行情接口 `fund_etf_spot_em()`。

```text
当前溢价率 = (最新价 / IOPV实时估值 - 1) × 100%
```

计算结果会与行情中的“基金折价率”反向交叉校验，误差超过 0.15 个百分点即判为整批异常。

- 较昨天：相对当前交易日之前最近一份有效快照。
- 较 30 天前：在“当前交易日减 30 个自然日”当天或之前寻找最近快照；早于目标超过 7 天则显示 `—`。
- 历史不足 30 天：显示 `—`，不补造历史行情。
- 周末：直接跳过。
- 工作日休市：当全部行情仍停留在此前交易日时跳过。
- 抓取或校验失败：有历史快照则整表回退并标注“缓存数据”；没有缓存则任务失败，不生成伪榜单。

## 本地运行

需要 Python 3.12。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
python -m etf_premium run
```

成功后会产生：

- `data/snapshots/YYYY-MM-DD.json`：版本化的有效行情快照；
- `site/index.html`：静态页面；
- `site/latest.png`：1080 像素宽中文排行榜；
- `site/latest.json`、`history.json` 和 `run_result.json`：结构化数据与运行状态。

若本机中文字体不在默认路径，可设置 `ETF_FONT_PATH` 指向一个支持中文的 TTF/TTC 字体。

## GitHub 配置

1. 创建公开仓库 `kevinzhouq/etf-premium-daily`，把本目录内容推送到默认分支。
2. 在仓库的 **Settings → Pages → Build and deployment** 中选择 **GitHub Actions**。
3. 在 **Settings → Secrets and variables → Actions** 新建 Secret `SERVERCHAN_SENDKEY`。
4. 打开 **Actions → ETF premium daily → Run workflow** 做首次手动验证。
5. 首次保持 `send_notification=false`；确认页面成功后，再设为 `true` 测试微信。

SendKey 只通过运行环境读取，不要写入 YAML、截图、Issue 或提交记录。

## 自动化行为

工作流位于 `.github/workflows/daily.yml`：

- `cron: "45 1 * * 1-5"`，即北京时间周一至周五 09:45（盘初观察）；
- `cron: "30 6 * * 1-5"`，即北京时间周一至周五 14:30（盘中决策参考）；
- `cron: "30 8 * * 1-5"`，即北京时间周一至周五 16:30（收盘归档）；
- 每次先执行离线测试和静态检查；
- 只有新鲜快照内容变化才提交 `data/snapshots/`；
- 页面部署完成后才发送带公开图片地址的正常通知；
- 定时任务默认通知，手动任务默认不通知；
- 构建或 Pages 部署失败时，发送不含图片的故障通知；
- 使用 concurrency 防止两个每日任务并发提交快照。

GitHub 的定时任务可能排队，因此页面展示实际抓取时间，而不是计划触发时间。

## 项目结构

```text
config/funds.yaml              基金池
src/etf_premium/               抓取、校验、历史、渲染和通知
tests/fixtures/etf_spot.json   九只基金的离线行情样本
tests/                         单元测试和离线集成测试
data/snapshots/                每日有效 JSON 快照
.github/workflows/daily.yml    定时、Pages 与 Server酱工作流
```

## 手动推送

先生成页面，再临时设置 `SERVERCHAN_SENDKEY` 和 `PAGE_URL=https://kevinzhouq.github.io/etf-premium-daily/`，然后运行：

```powershell
python -m etf_premium notify
```

## 许可证

MIT
