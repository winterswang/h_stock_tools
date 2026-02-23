#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本 - 生成可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


class Builder:
    """
    应用构建器
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化构建器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_file = self.project_root / "hkex_downloader.spec"
        
    def clean(self):
        """
        清理构建目录
        """
        print("清理构建目录...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        files_to_clean = [self.spec_file]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"已删除目录: {dir_path}")
        
        for file_path in files_to_clean:
            if file_path.exists():
                file_path.unlink()
                print(f"已删除文件: {file_path}")
    
    def check_dependencies(self) -> bool:
        """
        检查构建依赖
        
        Returns:
            依赖是否满足
        """
        print("检查构建依赖...")
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"PyInstaller版本: {PyInstaller.__version__}")
        except ImportError:
            print("错误: 未安装PyInstaller")
            print("请运行: pip install pyinstaller")
            return False
        
        # 检查项目依赖
        required_packages = [
            'requests', 'beautifulsoup4', 'lxml', 'pandas', 
            'click', 'pydantic', 'python-dateutil', 'tqdm',
            'aiohttp', 'aiofiles', 'pyyaml', 'akshare'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                # 特殊处理一些包名映射
                import_name = package
                if package == 'python-dateutil':
                    import_name = 'dateutil'
                elif package == 'beautifulsoup4':
                    import_name = 'bs4'
                elif package == 'pyyaml':
                    import_name = 'yaml'
                else:
                    import_name = package.replace('-', '_')
                __import__(import_name)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"错误: 缺少依赖包: {', '.join(missing_packages)}")
            print("请运行: pip install -r requirements.txt")
            return False
        
        print("所有依赖检查通过")
        return True
    
    def create_spec_file(self) -> Path:
        """
        创建PyInstaller规格文件
        
        Returns:
            规格文件路径
        """
        print("创建PyInstaller规格文件...")
        
        import akshare
        akshare_path = Path(akshare.__file__).parent
        
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{self.src_dir}/hkex_downloader_main.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('{self.project_root}/config', 'config'),
        ('{self.project_root}/docs', 'docs'),
        ('{akshare_path}/file_fold', 'akshare/file_fold'),
    ],
    hiddenimports=[
        'hkex_downloader',
        'hkex_downloader.api',
        'hkex_downloader.models',
        'hkex_downloader.services',
        'hkex_downloader.utils',
        'hkex_downloader.cli',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hkex-downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
        
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"规格文件已创建: {self.spec_file}")
        return self.spec_file
    
    def build_executable(self, onefile: bool = True, debug: bool = False) -> bool:
        """
        构建可执行文件
        
        Args:
            onefile: 是否打包为单个文件
            debug: 是否启用调试模式
        
        Returns:
            构建是否成功
        """
        print("开始构建可执行文件...")
        
        # 创建规格文件
        spec_file = self.create_spec_file()
        
        # 构建PyInstaller命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
        ]
        
        if debug:
            cmd.append('--debug=all')
        
        cmd.append(str(spec_file))
        
        print(f"执行命令: {' '.join(cmd)}")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.src_dir)
            
            # 执行构建
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("构建成功!")
                
                # 查找生成的可执行文件
                exe_path = self.dist_dir / "hkex-downloader"
                if exe_path.exists():
                    print(f"可执行文件位置: {exe_path}")
                    print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
                    
                    # 设置执行权限
                    exe_path.chmod(0o755)
                    print("已设置执行权限")
                    
                    return True
                else:
                    print("错误: 未找到生成的可执行文件")
                    return False
            else:
                print("构建失败!")
                print("错误输出:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"构建过程中出现异常: {e}")
            return False
    
    def create_dmg(self) -> bool:
        """
        创建macOS DMG安装包
        
        Returns:
            创建是否成功
        """
        print("创建DMG安装包...")
        
        exe_path = self.dist_dir / "hkex-downloader"
        if not exe_path.exists():
            print("错误: 可执行文件不存在，请先构建")
            return False
        
        # 检查是否在macOS上
        if sys.platform != 'darwin':
            print("警告: DMG创建仅支持macOS")
            return False
        
        # 创建临时目录
        temp_dir = self.dist_dir / "dmg_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # 复制可执行文件
        app_dir = temp_dir / "HKEx Downloader.app" / "Contents" / "MacOS"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(exe_path, app_dir / "hkex-downloader")
        
        # 创建Info.plist
        info_plist = temp_dir / "HKEx Downloader.app" / "Contents" / "Info.plist"
        info_plist.parent.mkdir(parents=True, exist_ok=True)
        
        plist_content = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>hkex-downloader</string>
    <key>CFBundleIdentifier</key>
    <string>com.hkex.downloader</string>
    <key>CFBundleName</key>
    <string>HKEx Downloader</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
'''
        
        with open(info_plist, 'w') as f:
            f.write(plist_content)
        
        # 创建DMG
        dmg_path = self.dist_dir / "HKEx-Downloader-1.0.0.dmg"
        
        cmd = [
            'hdiutil', 'create',
            '-volname', 'HKEx Downloader',
            '-srcfolder', str(temp_dir),
            '-ov', '-format', 'UDZO',
            str(dmg_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"DMG创建成功: {dmg_path}")
                
                # 清理临时目录
                shutil.rmtree(temp_dir)
                
                return True
            else:
                print("DMG创建失败:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"创建DMG时出现异常: {e}")
            return False
    
    def test_executable(self) -> bool:
        """
        测试可执行文件
        
        Returns:
            测试是否通过
        """
        print("测试可执行文件...")
        
        exe_path = self.dist_dir / "hkex-downloader"
        if not exe_path.exists():
            print("错误: 可执行文件不存在")
            return False
        
        # 测试版本信息
        try:
            result = subprocess.run(
                [str(exe_path), '--version'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"版本信息: {result.stdout.strip()}")
                print("可执行文件测试通过")
                return True
            else:
                print("可执行文件测试失败:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("可执行文件测试超时")
            return False
        except Exception as e:
            print(f"测试可执行文件时出现异常: {e}")
            return False
    
    def build_all(self, create_dmg: bool = True, debug: bool = False) -> bool:
        """
        完整构建流程
        
        Args:
            create_dmg: 是否创建DMG
            debug: 是否启用调试模式
        
        Returns:
            构建是否成功
        """
        print("开始完整构建流程...")
        print("=" * 50)
        
        # 1. 检查依赖
        if not self.check_dependencies():
            return False
        
        # 2. 清理
        self.clean()
        
        # 3. 构建可执行文件
        if not self.build_executable(debug=debug):
            return False
        
        # 4. 测试可执行文件
        if not self.test_executable():
            return False
        
        # 5. 创建DMG（仅macOS）
        if create_dmg and sys.platform == 'darwin':
            self.create_dmg()
        
        print("=" * 50)
        print("构建完成!")
        
        # 显示构建结果
        print("\n构建结果:")
        for item in self.dist_dir.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / 1024 / 1024
                print(f"  {item.name}: {size_mb:.1f} MB")
        
        return True


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="构建港交所文档下载工具")
    parser.add_argument('--clean', action='store_true', help='只清理构建目录')
    parser.add_argument('--no-dmg', action='store_true', help='不创建DMG')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--test-only', action='store_true', help='只测试可执行文件')
    
    args = parser.parse_args()
    
    builder = Builder()
    
    if args.clean:
        builder.clean()
        return
    
    if args.test_only:
        success = builder.test_executable()
        sys.exit(0 if success else 1)
    
    # 完整构建
    success = builder.build_all(
        create_dmg=not args.no_dmg,
        debug=args.debug
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()