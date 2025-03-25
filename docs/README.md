# 文档构建指南

## 安装依赖

```bash
pip install -r requirements.txt
```

请确保已经安装了完整版的开发环境

```bash
# 假设你在docs文件夹
pip install -e ..[all]
```

## 构建文档

```bash
make html
```

## 实时预览（开发模式）

```bash
make livehtml
```

启动后，文档将在 http://localhost:8000 自动打开。当您修改文档源文件时，页面会自动刷新。

注意事项：

1. 确保已安装所有依赖（包括 sphinx-autobuild）
2. 修改文件后保存即可看到实时更新
3. 按 Ctrl+C 停止实时预览服务器

## 文档结构

- `source/`: 文档源文件目录
- `build/`: 构建输出目录
- `_static/`: 静态资源文件
- `_templates/`: 自定义模板

## 常用命令

- `make clean`: 清理构建文件
- `make html`: 构建 HTML 文档
- `make livehtml`: 启动实时预览服务器
- `make publish`: 生成并发布文档到远程服务器
