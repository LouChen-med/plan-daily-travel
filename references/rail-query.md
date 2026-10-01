# 内置12306直达查询

在具备本地 Python 执行能力的 Codex 中，优先运行 scripts/query_rail.py，无需 MCP 或另装 Skill。手机、网页端没有本地脚本执行能力时，继续使用12306网页和携程。查询失败时明确记录失败，不解释为无票，并按 query-sources.md 切换入口。

## 环境
Python 3.10+，依赖 requests、可用的 Asia/Shanghai 时区数据。遵守用户的环境规范；依赖不存在时先说明并申请，不自动安装。本次验证环境为 brc_nerve_small，Python 3.11.15、requests 2.34.2，无新增依赖。其他电脑先核对自己的解释器。

本机示例（把技能根目录替换为实际路径）：

```powershell
& 'D:\software\Anaconda\Scripts\conda.exe' run -n brc_nerve_small python '<技能根目录>\scripts\query_rail.py' get-tickets --date 2026-10-06 --from_station 上海虹桥 --to_station 济南西 --train_filter_flags G --earliest_start_time 16 --limited_num 5 --format json
```

## 查询与解释
只支持已经准备的 get-tickets、list-tools、get-current-date。起终点必须为具体车站；严格筛选返回的实际车站电报码，排除同城其他车站；先筛选站点再限制条数。出发时间小时筛选只是候选初筛，完整门到门核算仍由规划流程执行。保留 queried_at、travel_date_requested、实际时刻、价格与席别库存。查询返回空列表不自动证明整座城市无车；改变车站前说明并征询用户。返回有车次不代表有合适席别，候补、无座不能当成二等座有票。

价格和余票随时变化，预订前复核。只查询，不购票。原版 start_date 使用列车始发日期推导，中途上车的跨日车次不能直接沿用其日期；以 travel_date_requested 为乘车日并另核验跨日到达。高铁结果不得替代接驳、候车和停止检票规则。

## 来源和适配
查询实现来自 https://github.com/Joooook/12306-skill ，保留原版 scripts/12306_apis.py 于 scripts/rail_vendor/12306_apis.py，来源代码未修改。本适配器避免直达查询依赖中转接口初始化，增加请求超时、HTTP错误检查、严格站点筛选和失败退出码。

本机原版入口因中转初始化跳转登录页而失败；适配器直达查询在2026-10-02实测成功。中转、经停和其他未验证功能不作为已具备能力宣称；对中转继续查询网页。完整源代码不代表未来网络和接口一定可用。
