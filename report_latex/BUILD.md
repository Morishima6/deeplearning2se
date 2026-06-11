# 编译说明

主文件：

```text
report_latex/final_report.tex
```

参考文献：

```text
report_latex/references.bib
```

建议使用 XeLaTeX 编译，因为模板依赖 `ctex` 处理中文。

## 编译命令

在 `report_latex/` 目录下执行：

```bash
xelatex final_report.tex
bibtex final_report
xelatex final_report.tex
xelatex final_report.tex
```

如果使用 TeXstudio 或 VS Code LaTeX Workshop，编译链选择：

```text
XeLaTeX -> BibTeX -> XeLaTeX -> XeLaTeX
```

## 当前图表状态

`final_report.tex` 目前包含 4 个图表占位框，不会阻塞编译。需要手工制作的图片见：

```text
report_latex/figures_to_make.md
```

制作图片后，按该文件中的替换示例把 `\figuretodo{...}` 换成 `\includegraphics`。

## 说明

本机当前未检测到 `xelatex` 和 `bibtex` 命令，因此还没有在 Windows 本地完成 PDF 编译验证。建议在装有 TeX Live / MiKTeX 的本地或服务器环境中运行上述命令。
