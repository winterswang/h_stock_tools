# 财务数据功能说明

本文档介绍hkex_downloader新增的财务数据下载和处理功能。

## 功能概述

基于akshare库，hkex_downloader现在支持获取和下载港股上市公司的财务数据，包括：

- **资产负债表** (Balance Sheet)
- **利润表** (Income Statement) 
- **现金流量表** (Cash Flow Statement)
- **财务指标** (Financial Indicators)

## 主要特性

### 1. 数据获取
- 支持通过akshare获取港股财务数据
- 提供统一的API接口
- 支持多种报表类型和报告期

### 2. 数据格式化
- 中英文字段映射
- 数值格式标准化
- 日期格式统一
- 单位转换支持

### 3. 数据导出
- 支持CSV、Excel、JSON格式
- 可选择中文或英文字段名
- 支持按股票代码组织文件夹
- 批量下载功能

### 4. 命令行工具
- 提供便捷的CLI命令
- 支持单个和批量下载
- 数据预览功能

## 快速开始

### 安装依赖

```bash
pip install akshare>=1.12.0
```

### 基本使用

#### 1. 获取单个股票的财务数据

```python
from hkex_downloader import FinancialDataService, FinancialDataRequest, ReportType

# 创建服务
service = FinancialDataService()

# 创建请求
request = FinancialDataRequest(
    stock_code="00700",  # 腾讯
    report_type=ReportType.BALANCE_SHEET,
    limit=5
)

# 获取数据
response = service.get_financial_report(request)

if response.success:
    for data in response.data.data_list:
        print(f"报告期: {data.report_date}")
        print(f"总资产: {data.total_assets:,.0f}")
```

#### 2. 下载财务数据到文件

```python
from hkex_downloader import FinancialDataDownloader

# 创建下载器
downloader = FinancialDataDownloader(download_dir="./financial_data")

# 下载数据
result = downloader.download_financial_data(
    request=request,
    format_type="csv",
    use_english_fields=True
)

if result.success:
    print(f"文件已保存: {result.file_path}")
```

#### 3. 批量下载

```python
# 批量下载多个股票的财务数据
results = downloader.download_batch_financial_data(
    stock_codes=["00700", "03690", "00981"],
    report_types=[ReportType.BALANCE_SHEET, ReportType.INCOME_STATEMENT],
    format_type="csv"
)
```

## 命令行使用

### 下载单个股票的财务数据

```bash
# 下载腾讯的所有财务数据
python -m hkex_downloader download-financial 00700

# 下载指定类型的数据
python -m hkex_downloader download-financial 00700 -t balance_sheet

# 指定输出格式和目录
python -m hkex_downloader download-financial 00700 -f excel -d ./data
```

### 批量下载

```bash
# 批量下载多个股票的财务数据
python -m hkex_downloader batch-download-financial 00700 03690 00981

# 指定报表类型
python -m hkex_downloader batch-download-financial 00700 03690 -t balance_sheet -t income_statement
```

### 查看财务数据

```bash
# 查看财务数据（不下载）
python -m hkex_downloader show-financial 00700 -t balance_sheet
```

## API参考

### 核心类

#### FinancialDataService
财务数据服务类，负责从akshare获取数据。

```python
class FinancialDataService:
    def get_financial_report(self, request: FinancialDataRequest) -> FinancialDataResponse
    def get_all_financial_data(self, stock_code: str, limit: Optional[int] = None) -> FinancialDataResponse
```

#### FinancialDataDownloader
财务数据下载器，负责数据格式化和文件保存。

```python
class FinancialDataDownloader:
    def download_financial_data(self, request: FinancialDataRequest, **kwargs) -> FinancialDownloadResult
    def download_all_financial_data(self, stock_code: str, **kwargs) -> List[FinancialDownloadResult]
    def download_batch_financial_data(self, stock_codes: List[str], **kwargs) -> Dict[str, List[FinancialDownloadResult]]
```

#### FinancialDataFormatter
数据格式化工具，提供字段映射和数据转换。

```python
class FinancialDataFormatter:
    def format_financial_data(self, data: FinancialData, use_english_fields: bool = True) -> Dict[str, Any]
    def format_dataframe(self, df: DataFrame, use_english_fields: bool = True) -> DataFrame
```

### 数据模型

#### ReportType (报表类型)
- `BALANCE_SHEET`: 资产负债表
- `INCOME_STATEMENT`: 利润表
- `CASH_FLOW`: 现金流量表
- `FINANCIAL_INDICATORS`: 财务指标

#### ReportPeriod (报告期类型)
- `ANNUAL`: 年报
- `INTERIM`: 中报
- `QUARTERLY`: 季报

## 字段映射

### 资产负债表主要字段

| 中文字段 | 英文字段 | 说明 |
|---------|---------|------|
| 总资产 | total_assets | 资产总计 |
| 总负债 | total_liabilities | 负债总计 |
| 股东权益合计 | total_equity | 股东权益总计 |
| 流动资产合计 | current_assets | 流动资产总计 |
| 流动负债合计 | current_liabilities | 流动负债总计 |
| 货币资金 | cash_and_equivalents | 现金及现金等价物 |
| 应收账款 | accounts_receivable | 应收账款 |
| 存货 | inventory | 存货 |
| 固定资产 | fixed_assets | 固定资产 |
| 无形资产 | intangible_assets | 无形资产 |

### 利润表主要字段

| 中文字段 | 英文字段 | 说明 |
|---------|---------|------|
| 营业总收入 | total_revenue | 营业总收入 |
| 营业成本 | operating_costs | 营业成本 |
| 毛利润 | gross_profit | 毛利润 |
| 营业利润 | operating_profit | 营业利润 |
| 利润总额 | total_profit | 利润总额 |
| 净利润 | net_profit | 净利润 |
| 基本每股收益 | basic_eps | 基本每股收益 |

### 现金流量表主要字段

| 中文字段 | 英文字段 | 说明 |
|---------|---------|------|
| 经营活动现金流量净额 | operating_cash_flow | 经营活动现金流量净额 |
| 投资活动现金流量净额 | investing_cash_flow | 投资活动现金流量净额 |
| 筹资活动现金流量净额 | financing_cash_flow | 筹资活动现金流量净额 |
| 现金及现金等价物净增加额 | net_cash_flow | 现金及现金等价物净增加额 |

### 财务指标主要字段

| 中文字段 | 英文字段 | 说明 |
|---------|---------|------|
| 净资产收益率 | roe | 净资产收益率 |
| 总资产收益率 | roa | 总资产收益率 |
| 流动比率 | current_ratio | 流动比率 |
| 资产负债率 | debt_to_equity_ratio | 资产负债率 |
| 每股收益 | eps | 每股收益 |
| 市盈率 | pe_ratio | 市盈率 |
| 市净率 | pb_ratio | 市净率 |

## 配置选项

### 下载配置

```yaml
# config/default.yaml
financial:
  download_dir: "./data/financial"  # 财务数据下载目录
  default_format: "csv"             # 默认输出格式
  use_english_fields: true          # 默认使用英文字段名
  organize_by_stock: true           # 按股票代码组织文件夹
  cache_enabled: true               # 启用缓存
  cache_ttl_hours: 24              # 缓存有效期（小时）
```

## 注意事项

1. **网络依赖**: 财务数据获取需要网络连接，依赖akshare库的数据源。

2. **数据延迟**: 财务数据可能存在一定延迟，具体以数据源为准。

3. **股票代码格式**: 使用港股标准格式，如"00700"（腾讯）。

4. **数据完整性**: 不同股票的财务数据完整性可能不同，部分字段可能为空。

5. **频率限制**: 请合理使用，避免过于频繁的请求。

## 错误处理

```python
try:
    response = service.get_financial_report(request)
    if not response.success:
        print(f"获取数据失败: {response.message}")
except Exception as e:
    print(f"发生错误: {e}")
```

## 示例代码

完整的使用示例请参考 `examples/financial_data_example.py` 文件。

## 更新日志

### v1.1.0
- 新增财务数据获取功能
- 支持三大财务报表和财务指标
- 提供数据格式化和导出功能
- 新增CLI命令支持
- 完善的中英文字段映射

## 技术支持

如有问题或建议，请提交Issue或联系开发团队。