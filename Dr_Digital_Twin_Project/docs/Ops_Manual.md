# 数字孪生医生系统运维与灾备手册 (Ops & Disaster Recovery Manual)

## 1. 监控告警体系 (Monitoring & Alerting)

### 1.1 监控选型与层级
- **基础设施层 (Infrastructure)**：使用 Prometheus 抓取 Kubernetes Node/Pod 级别指标 (CPU, 内存, 网络 I/O, 磁盘 IOPS)。
- **应用服务层 (Application)**：使用 Prometheus Client 库统计 FastAPI 的 TPS (单实例并发目标 $\ge 1000$), 接口 P95/P99 延迟 (目标 $\le 300$ ms)，错误率 (HTTP 5xx)。
- **AI与模型层 (AI & Twin Models)**：监控 vLLM / TensorRT-LLM 的 GPU 显存利用率 (VRAM)，Token 生成速度 (Tokens/sec)，以及预测误差的漂移率。
- **展示面板**：Grafana 提供定制化的 SRE 监控大屏。

### 1.2 告警策略
- **阈值设定**：
  - HTTP 500 错误率 $> 1\%$ 持续 1 分钟 $\rightarrow$ **P1 告警 (钉钉/飞书/电话)**。
  - API P99 响应延迟 $> 500$ ms 持续 3 分钟 $\rightarrow$ **P2 告警 (短信/工作群)**。
  - GPU 显存利用率 $> 90\%$ 持续 5 分钟 $\rightarrow$ **P3 告警 (邮件)**。

## 2. 日志规范 (Logging Standard)
- **收集与存储**：采用 ELK Stack (Elasticsearch, Logstash, Kibana) 或 Fluentd/Fluent Bit 收集微服务日志。
- **日志格式**：强制要求 JSON 结构化输出。必须包含：
  - `trace_id`: 全链路追踪 ID (集成 OpenTelemetry/Jaeger)。
  - `patient_id` (哈希掩码后): 关联数据主体。
  - `level`: DEBUG/INFO/WARN/ERROR/FATAL。
  - `timestamp`: ISO8601 标准时间戳。

## 3. 灾备方案与业务连续性 (Disaster Recovery & BCP)

### 3.1 核心目标 (SLA)
本系统支持 ICU 级模拟与急救场景，业务连续性指标必须满足：
- **RPO (Recovery Point Objective) $\le 15$ 分钟**。
- **RTO (Recovery Time Objective) $\le 30$ 分钟**。
- **SLA 可用性 $\ge 99.9\%$** ($7 \times 24$ 小时稳定运行)。

### 3.2 异地多活与备份策略
- **数据库同步**：PostgreSQL (关系型数据) 采用一主多从架构，通过 Write-Ahead Logging (WAL) 实现跨可用区 (Multi-AZ) 的半同步复制。
- **TSDB 备份**：InfluxDB/TimescaleDB 数据每 10 分钟执行一次增量快照备份至对象存储 (S3 兼容)。
- **流量切换**：前端与网关层 (Nginx/Envoy) 结合 DNS 解析/Global Load Balancer 实现故障区域流量在 3 分钟内自动切换至备用机房。

## 4. 持续集成与部署 (CI/CD GitOps 流水线)

### 4.1 代码构建与质量扫描
- **代码库**：GitLab 或 GitHub。
- **扫描周期**：自动化构建、镜像扫描（Trivy）、依赖漏洞修复的闭环周期 $\le 24$ 小时。
- **测试覆盖率**：要求 `pytest` 单元测试覆盖率 $\ge 90\%$，自动化集成测试用例 $\ge 200$ 条（必须包含边界值、网络断连异常、高并发性能场景）。

### 4.2 GitOps 部署流程
- **工具链**：ArgoCD 或 FluxCD。
- **环境隔离**：区分 DEV (开发), STG (集成测试), UAT (预发布), PROD (生产)。
- **灰度发布**：针对 AI 模型更新（尤其是深度学习诊疗算法），强制采用蓝绿部署或金丝雀发布 (Canary Release)，在 STG 环境下通过临床医生盲测（目标可用性评分 $\ge 4.5/5$），并在 1000 例历史脱敏数据上回归测试，确保预测误差 MAPE $\le 8\%$，方可合入 PROD 主干。
