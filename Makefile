# 港交所文档下载工具 Makefile

.PHONY: help install dev-install test lint format clean build build-debug build-dmg run-tests package

# 默认目标
help:
	@echo "港交所文档下载工具 - 可用命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  install      - 安装项目依赖"
	@echo "  dev-install  - 安装开发依赖"
	@echo "  test         - 运行测试"
	@echo "  lint         - 代码检查"
	@echo "  format       - 代码格式化"
	@echo ""
	@echo "构建:"
	@echo "  clean        - 清理构建文件"
	@echo "  build        - 构建可执行文件"
	@echo "  build-debug  - 构建调试版本"
	@echo "  build-dmg    - 构建DMG安装包 (仅macOS)"
	@echo "  package      - 完整打包流程"
	@echo ""
	@echo "运行:"
	@echo "  run-help     - 显示帮助信息"
	@echo "  run-test-api - 测试API接口"
	@echo ""

# 安装依赖
install:
	@echo "安装项目依赖..."
	pip install -e .

dev-install: install
	@echo "安装开发依赖..."
	pip install -e ".[dev,build]"

# 测试
test:
	@echo "运行测试..."
	pytest tests/ -v

run-tests: test

# 代码质量
lint:
	@echo "运行代码检查..."
	flake8 src/ tests/
	mypy src/

format:
	@echo "格式化代码..."
	black src/ tests/
	isort src/ tests/

# 清理
clean:
	@echo "清理构建文件..."
	python scripts/build.py --clean
	rm -rf __pycache__ .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 构建
build: clean
	@echo "构建可执行文件..."
	python scripts/build.py --no-dmg

build-debug: clean
	@echo "构建调试版本..."
	python scripts/build.py --debug --no-dmg

build-dmg: clean
	@echo "构建DMG安装包..."
	python scripts/build.py

package: clean lint test build-dmg
	@echo "完整打包流程完成!"

# 运行
run-help:
	@echo "显示帮助信息..."
	python -m hkex_downloader.cli.main --help

run-test-api:
	@echo "测试API接口..."
	python test_api.py

# 快速命令
quick-build: build

quick-test:
	@echo "快速测试..."
	python test_api.py

# 安装到系统
install-system:
	@echo "安装到系统..."
	pip install .

uninstall-system:
	@echo "从系统卸载..."
	pip uninstall hkex-downloader -y

# 开发服务器
dev-server:
	@echo "启动开发环境..."
	python -m hkex_downloader.cli.main --verbose

# 文档
docs:
	@echo "生成文档..."
	@echo "文档位于 docs/ 目录"

# 版本信息
version:
	@echo "显示版本信息..."
	python -c "from src.hkex_downloader import __version__; print(__version__)"

# 检查环境
check-env:
	@echo "检查Python环境..."
	@python --version
	@echo "检查pip版本..."
	@pip --version
	@echo "检查已安装的包..."
	@pip list | grep -E "(requests|click|pydantic|aiohttp)"

# 示例命令
example-ipo:
	@echo "示例: 搜索IPO招股书..."
	python -m hkex_downloader.cli.main search-ipo -f 20240101 -t 20241231 --download

example-annual:
	@echo "示例: 搜索年度业绩公告..."
	python -m hkex_downloader.cli.main search-annual -f 20240101 -t 20241231 -s 00700

example-stock:
	@echo "示例: 搜索股票信息..."
	python -m hkex_downloader.cli.main search-stock 00700

# 性能测试
perf-test:
	@echo "运行性能测试..."
	time python test_api.py

# 内存测试
memory-test:
	@echo "运行内存测试..."
	@which valgrind > /dev/null && valgrind --tool=memcheck python test_api.py || echo "valgrind未安装，跳过内存测试"

# 发布准备
release-check: lint test
	@echo "发布前检查..."
	@echo "✓ 代码检查通过"
	@echo "✓ 测试通过"
	@echo "准备发布!"

# 备份
backup:
	@echo "创建项目备份..."
	tar -czf "hkex-downloader-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz" \
		--exclude="dist" --exclude="build" --exclude="__pycache__" \
		--exclude=".git" --exclude="*.pyc" .

# 统计
stats:
	@echo "项目统计信息:"
	@echo "Python文件数量: $(shell find src/ -name '*.py' | wc -l)"
	@echo "代码行数: $(shell find src/ -name '*.py' -exec wc -l {} + | tail -1)"
	@echo "测试文件数量: $(shell find tests/ -name '*.py' 2>/dev/null | wc -l || echo 0)"

# 依赖更新
update-deps:
	@echo "更新依赖包..."
	pip list --outdated
	@echo "运行 'pip install --upgrade <package>' 来更新特定包"

# 安全检查
security-check:
	@echo "运行安全检查..."
	@which safety > /dev/null && safety check || echo "safety未安装，跳过安全检查"
	@which bandit > /dev/null && bandit -r src/ || echo "bandit未安装，跳过安全检查"