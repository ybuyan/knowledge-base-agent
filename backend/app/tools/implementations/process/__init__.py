"""
流程 Tools 自动注册

目录结构约定：
  process/
    base_nodes.py          通用节点（任何流程可用）
    <flow_name>/           流程专属目录
      <tool_name>.py       该流程的专属 Tool

新增流程只需在此目录下建子目录并写 Tool 文件，无需修改本文件。
"""
import importlib
import pkgutil
from pathlib import Path


def _auto_import():
    """递归导入 process/ 下所有 .py 模块，触发 @ToolRegistry.register 装饰器"""
    package_dir = Path(__file__).parent
    package_name = __name__  # app.tools.implementations.process

    for finder, module_name, is_pkg in pkgutil.walk_packages(
        path=[str(package_dir)],
        prefix=package_name + ".",
        onerror=lambda x: None,
    ):
        importlib.import_module(module_name)


_auto_import()
