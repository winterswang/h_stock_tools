# 港交所文档下载工具 (HKEx Downloader)

一个专业的港交所上市公司信息查询和下载工具，支持IPO招股书、年度业绩公告、中期业绩公告等文档的批量下载。

## 🌟 主要特性

- **多类型文档支持**: IPO招股书、年度业绩公告、中期业绩公告
- **智能股票解析**: 自动将股票代码转换为港交所内部ID
- **高效批量下载**: 支持异步并发下载，提高下载效率
- **灵活的搜索条件**: 支持按日期范围、股票代码等条件搜索
- **完善的缓存机制**: 减少重复API调用，提高响应速度
- **命令行界面**: 简单易用的CLI工具
- **一键打包**: 支持生成Mac可执行文件和DMG安装包
- **详细的日志记录**: 完整的操作日志和错误追踪

## 📋 系统要求

- Python 3.8+
- macOS 10.14+ (推荐)
- 网络连接

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd hstock_dw

# 安装依赖
pip install -r requirements.txt

# 或使用Makefile
make install
```

### 基本使用

#### 1. 搜索IPO招股书

```bash
# 搜索2024年的IPO招股书
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231

# 搜索特定公司的IPO招股书并直接下载
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231 -s 00700 --download
```

#### 2. 搜索业绩公告

```bash
# 搜索年度业绩公告
python -m hkex_downloader.cli.main search-annual -f 20240101 -t 20241231

# 搜索中期业绩公告
python -m hkex_downloader.cli.main search-interim -f 20240101 -t 20241231
```

#### 3. 股票信息查询

```bash
# 查询股票信息
python -m hkex_downloader.cli.main search-stock 00700
```

#### 4. 快速下载

```bash
# 一键下载所有类型文档
python -m hkex_downloader.cli.main quick-download -f 20240101 -t 20241231

# 批量下载多个股票的文档
python -m hkex_downloader.cli.main batch-download 00700 00981 01024 -f 20240101 -t 20241231
```

## 🛠️ 构建可执行文件

### 使用Makefile（推荐）

```bash
# 安装构建依赖
make dev-install

# 构建可执行文件
make build

# 构建DMG安装包（仅macOS）
make build-dmg

# 完整打包流程（包含测试和代码检查）
make package
```

### 使用构建脚本

```bash
# 安装PyInstaller
pip install pyinstaller

# 运行构建脚本
python scripts/build.py

# 仅构建可执行文件（不创建DMG）
python scripts/build.py --no-dmg

# 构建调试版本
python scripts/build.py --debug
```

构建完成后，可执行文件位于 `dist/` 目录中。

## 📁 项目结构

```
hstock_dw/
├── src/hkex_downloader/          # 主要源代码
│   ├── api/                      # API客户端
│   ├── models/                   # 数据模型
│   ├── services/                 # 业务服务
│   ├── utils/                    # 工具函数
│   └── cli/                      # 命令行界面
├── config/                       # 配置文件
├── data/                         # 数据目录
│   ├── cache/                    # 缓存文件
│   ├── downloads/                # 下载文件
│   └── exports/                  # 导出文件
├── logs/                         # 日志文件
├── scripts/                      # 构建脚本
├── tests/                        # 测试文件
├── docs/                         # 文档
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
├── Makefile                     # 构建命令
└── README.md                    # 项目说明
```

## ⚙️ 配置

项目使用YAML格式的配置文件，默认配置位于 `config/default.yaml`。

主要配置项：

```yaml
# API配置
api:
  timeout: 30                    # 请求超时时间
  max_retries: 3                 # 最大重试次数
  backoff_factor: 0.3            # 重试间隔因子

# 下载配置
download:
  download_dir: "./downloads"     # 下载目录
  max_concurrent: 5              # 最大并发数
  pdf_only: true                 # 仅下载PDF
  organize_by_company: true      # 按公司组织文件夹

# 缓存配置
cache:
  cache_dir: "./cache"           # 缓存目录
  cache_ttl_hours: 24            # 缓存有效期
  enable_cache: true             # 启用缓存

# 日志配置
logging:
  log_level: "INFO"              # 日志级别
  log_dir: "./logs"              # 日志目录
  console_output: true           # 控制台输出
```

## 📖 API文档

### 核心类

#### HKExClient
港交所API客户端，提供基础的API调用功能。

```python
from hkex_downloader import HKExClient

client = HKExClient()
# 搜索股票
response = client.search_stock("00700")
# 搜索IPO文档
response = client.search_ipo_documents("20240101", "20241231")
```

#### DocumentSearcher
文档搜索服务，提供高级搜索功能。

```python
from hkex_downloader import DocumentSearcher

searcher = DocumentSearcher()
# 搜索IPO招股书
response = searcher.search_ipo_prospectus(
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31),
    stock_code="00700"
)
```

#### DocumentDownloader
文档下载服务，支持批量和异步下载。

```python
from hkex_downloader import DocumentDownloader

downloader = DocumentDownloader(download_dir="./downloads")
# 下载搜索结果
results = downloader.download_search_results(response)
```

#### StockResolver
股票解析服务，提供股票代码到ID的转换。

```python
from hkex_downloader.services import StockResolver

resolver = StockResolver()
# 解析股票ID
stock_id = resolver.resolve_stock_id("00700")
# 获取公司信息
company = resolver.resolve_company_info("00700")
```

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行API测试
make run-test-api

# 代码检查
make lint

# 代码格式化
make format
```

## 📝 使用示例

### 示例1：下载腾讯的所有业绩公告

```bash
python -m hkex_downloader.cli.main search-annual -f 20230101 -t 20231231 -s 00700 --download
```

### 示例2：批量下载多个公司的IPO招股书

```bash
python -m hkex_downloader.cli.main batch-download 00700 00981 01024 -f 20240101 -t 20241231
```

### 示例3：编程方式使用

```python
from datetime import date
from hkex_downloader import DocumentSearcher, DocumentDownloader

# 创建服务实例
searcher = DocumentSearcher()
downloader = DocumentDownloader()

# 搜索文档
response = searcher.search_ipo_prospectus(
    from_date=date(2024, 1, 1),
    to_date=date(2024, 12, 31)
)

print(f"找到 {len(response.documents)} 个IPO文档")

# 下载文档
if response.documents:
    results = downloader.download_search_results(response)
    success_count = sum(1 for r in results if r.success)
    print(f"成功下载 {success_count} 个文档")
```

## 🔧 故障排除

### 常见问题

1. **网络连接问题**
   - 检查网络连接
   - 确认可以访问 `https://www1.hkexnews.hk`
   - 尝试增加超时时间

2. **下载失败**
   - 检查磁盘空间
   - 确认下载目录权限
   - 查看日志文件获取详细错误信息

3. **构建失败**
   - 确认已安装PyInstaller: `pip install pyinstaller`
   - 检查Python版本是否为3.8+
   - 查看构建日志获取详细错误信息

### 日志文件

日志文件位于 `logs/hkex_downloader.log`，包含详细的操作记录和错误信息。

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 港交所提供的公开API
- Python开源社区的优秀库
- 所有贡献者的支持

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**注意**: 本工具仅用于学习和研究目的，请遵守港交所的使用条款和相关法律法规。