# Books & Thoughts

和 Claude 一起读书，记录思考与对话。

## 使用方式

1. 用 `tools/convert.py` 把书转成 Markdown（见下方）
2. 将转换后的 `.md` 文件上传给 Claude
3. Claude 逐章提供摘要和核心思想
4. 基于 Claude 的总结提出问题，展开对话
5. 将思考和笔记记录在对应书籍的文件夹中

## 格式转换工具

支持 PDF / EPUB / MOBI / AZW3，统一转为 Markdown 后上传 Claude。

**第一次使用：**
```bash
bash tools/setup.sh
```

**转换单本书：**
```bash
python3 tools/convert.py book.epub
python3 tools/convert.py book.pdf -o ./tech/my-book/
```

**批量转换整个文件夹：**
```bash
python3 tools/convert.py ~/Downloads/books/ -o ./converted/
```

> MOBI / AZW3 需要安装 Calibre（`setup.sh` 会询问是否安装）。

## 书籍分类

| 文件夹 | 类别 | 说明 |
|--------|------|------|
| [tech](./tech/) | 技术 / 编程 | 计算机、软件工程、AI |
| [business](./business/) | 商业 / 管理 | 创业、战略、经济学 |
| [psychology](./psychology/) | 心理学 / 行为科学 | 认知、决策、人际 |
| [philosophy](./philosophy/) | 哲学 / 思想 | 伦理、逻辑、世界观 |
| [history](./history/) | 历史 / 传记 | 历史事件、人物传记 |
| [science](./science/) | 科普 / 自然科学 | 物理、生物、宇宙 |
| [self-improvement](./self-improvement/) | 自我提升 | 效率、习惯、成长 |
| [fiction](./fiction/) | 小说 / 文学 | 经典文学、当代小说 |

## 笔记模板

每本书在对应分类下新建一个文件夹，参考 [_template](./_template/README.md)。
