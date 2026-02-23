# 快速开始指南

本指南将帮助您快速上手港交所文档下载工具。

## 📦 安装

### 方法1: 从源码安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd hstock_dw

# 2. 安装依赖
pip install -r requirements.txt

# 3. 测试安装
python -m hkex_downloader.cli.main --help
```

### 方法2: 使用可执行文件

如果您有预编译的可执行文件：

```bash
# macOS
./hkex-downloader --help

# 或者从DMG安装后
/Applications/HKEx\ Downloader.app/Contents/MacOS/hkex-downloader --help
```

## 🚀 第一次使用

### 1. 查看帮助信息

```bash
python -m hkex_downloader.cli.main --help
```

### 2. 搜索股票信息

```bash
# 搜索腾讯股票信息
python -m hkex_downloader.cli.main search-stock 00700
```

输出示例：
```
找到 1 个匹配的股票:

 1. 00700 - 腾讯控股有限公司
    股票ID: 700
```

### 3. 搜索IPO招股书

```bash
# 搜索2024年的IPO招股书
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231
```

### 4. 搜索业绩公告

```bash
# 搜索腾讯2024年的年度业绩公告
python -m hkex_downloader.cli.main search-annual -f 20240101 -t 20241231 -s 00700
```

### 5. 直接下载文档

```bash
# 搜索并直接下载IPO招股书
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231 --download
```

## 🎯 常用命令

### 快速下载

一键下载所有类型的文档：

```bash
# 下载2024年所有文档
python -m hkex_downloader.cli.main quick-download -f 20240101 -t 20241231

# 下载特定公司的文档
python -m hkex_downloader.cli.main quick-download -f 20240101 -t 20241231 -s 00700
```

### 批量下载

为多个公司批量下载文档：

```bash
# 批量下载腾讯、中芯国际、快手的文档
python -m hkex_downloader.cli.main batch-download 00700 00981 01024 -f 20240101 -t 20241231
```

### 保存搜索结果

将搜索结果保存为JSON文件：

```bash
# 搜索并保存结果
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231 -o ipo_results.json

# 从JSON文件下载
python -m hkex_downloader.cli.main download-documents ipo_results.json
```

## 📁 文件组织

默认情况下，下载的文件会按以下结构组织：

```
downloads/
├── IPO招股书/
│   ├── 00700_20240315_腾讯控股申请版本.pdf
│   └── 00981_20240220_中芯国际申请版本.pdf
├── 年度业绩公告/
│   ├── 00700_20240320_腾讯控股年度业绩.pdf
│   └── 00981_20240318_中芯国际年度业绩.pdf
└── 中期业绩公告/
    ├── 00700_20240815_腾讯控股中期业绩.pdf
    └── 00981_20240810_中芯国际中期业绩.pdf
```

## ⚙️ 基本配置

### 修改下载目录

```bash
# 指定下载目录
python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231 --download-dir /path/to/downloads
```

### 启用详细输出

```bash
# 显示详细信息
python -m hkex_downloader.cli.main --verbose search-ipo -f 20240101 -t 20241231
```

## 🔧 故障排除

### 常见错误

1. **模块未找到错误**
   ```bash
   # 确保在项目根目录运行
   cd hstock_dw
   python -m hkex_downloader.cli.main --help
   ```

2. **网络连接错误**
   ```bash
   # 检查网络连接
   ping www1.hkexnews.hk
   ```

3. **权限错误**
   ```bash
   # 确保有写入权限
   mkdir -p downloads
   chmod 755 downloads
   ```

### 查看日志

```bash
# 查看日志文件
tail -f logs/hkex_downloader.log
```

## 📚 进阶使用

### 编程方式使用

创建一个Python脚本：

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

### 自定义配置

创建配置文件 `config.yaml`：

```yaml
download:
  download_dir: "/Users/yourname/HKEx_Documents"
  max_concurrent: 3
  pdf_only: true

logging:
  log_level: "DEBUG"
  console_output: true
```

使用自定义配置：

```bash
python -m hkex_downloader.cli.main -c config.yaml search-ipo -f 20240101 -t 20241231
```

## 🎉 完成！

现在您已经掌握了港交所文档下载工具的基本使用方法。更多高级功能请参考：

- [完整文档](README.md)
- [API文档](API.md)
- [配置指南](CONFIGURATION.md)
- [示例代码](../examples/)

如有问题，请查看[故障排除指南](TROUBLESHOOTING.md)或提交Issue。