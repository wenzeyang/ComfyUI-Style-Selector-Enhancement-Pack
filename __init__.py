"""Style selector derived from yolain/ComfyUI-Easy-Use 1.4.1 (GPL-3.0)."""
import json
import os
from pathlib import Path
from aiohttp import web
from server import PromptServer
from comfy_api.latest import io, ComfyExtension

ROOT = Path(__file__).resolve().parent
FOOOCUS_STYLES_DIR = str(ROOT / "styles")
WEB_DIRECTORY = "./web"


def read_styles(name):
    allowed = {p.stem: p for p in (ROOT / "styles").glob("*.json") if not p.name.endswith("_cn.json")}
    if name not in allowed:
        raise ValueError("Unknown style library")
    data = json.loads(allowed[name].read_text(encoding="utf-8-sig"))
    if not isinstance(data, list) or any(not isinstance(s, dict) or not isinstance(s.get("name"), str) for s in data):
        raise ValueError("Style library must be a list of objects with string names")
    return data


@PromptServer.instance.routes.get("/style-selector-enhancement/styles")
async def list_styles(request):
    try:
        data = read_styles(request.query.get("name", ""))
    except (ValueError, OSError) as error:
        return web.json_response({"error": str(error)}, status=400)
    result = []
    from urllib.parse import urlencode
    for index, style in enumerate(data):
        item = {k: style[k] for k in ("name", "name_cn", "prompt", "negative_prompt") if k in style}
        if style.get('thumbnail'):
            item['thumbnail'] = '/style-selector-enhancement/thumbnail?' + urlencode({'name': request.query['name'], 'index': index})
        result.append(item)
    return web.json_response(result)


@PromptServer.instance.routes.get('/style-selector-enhancement/thumbnail')
async def thumbnail(request):
    try:
        data = read_styles(request.query.get('name', ''))
        index = int(request.query.get('index', '-1'))
        if not 0 <= index < len(data):
            raise ValueError('Invalid index')
        value = data[index].get('thumbnail', '')
        if isinstance(value, list):
            value = value[0] if value else ''
        root = (ROOT / 'styles').resolve()
        path = (root / value).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'} or not path.is_file():
            raise ValueError('Invalid thumbnail')
        return web.FileResponse(path)
    except (ValueError, TypeError, OSError):
        raise web.HTTPNotFound()


class StyleSelectorEnhancement(io.ComfyNode):

    @classmethod
    def define_schema(cls):
        styles = []
        styles_dir = FOOOCUS_STYLES_DIR
        for file_name in sorted(os.listdir(styles_dir)):
            file = os.path.join(styles_dir, file_name)
            if os.path.isfile(file) and file_name.endswith(".json"):
                if not file_name.endswith("_cn.json"):
                    styles.append(file_name.split(".")[0])

        return io.Schema(
            node_id="StyleSelectorEnhancement",
            display_name="风格选择器增强 / Style Selector",
            category="Style Selector",
            inputs=[
                io.Combo.Input("styles", options=styles, default=styles[0] if styles else "example"),
                io.String.Input("positive", default="", force_input=True, optional=True),
                io.String.Input("negative", default="", force_input=True, optional=True),
                io.String.Input("select_styles", default="", optional=True),
                io.Combo.Input("selection_mode", options=["多选模式（叠加）", "单选模式", "多选模式（逐一生成）", "全选模式"], default="多选模式（叠加）", optional=True),
                io.String.Input("filename_prefix", default="Krea2-%date:yyyyMMddhhmmss%", optional=True),
            ],
            outputs=[
                io.String.Output(id="output_positive", display_name="positive", is_output_list=True),
                io.String.Output(id="output_negative", display_name="negative", is_output_list=True),
                io.String.Output(id="style_filename", display_name="文件名前缀", is_output_list=True),
            ],
            hidden=[
                io.Hidden.prompt,
                io.Hidden.extra_pnginfo,
                io.Hidden.unique_id,
            ],
        )

    @classmethod
    def execute(cls, styles, positive='', negative='', select_styles=None, selection_mode="多选模式（叠加）", filename_prefix="Krea2-%date:yyyyMMddhhmmss%", **kwargs):
        values = []
        all_styles = {}
        positive_prompt, negative_prompt = '', negative
        data = read_styles(styles)
        for d in data:
            all_styles[d['name']] = d
        if isinstance(select_styles, str):
            values = select_styles.split(',')
        else:
            values = list(select_styles) if select_styles else []
        if selection_mode == "全选模式" and select_styles is None:
            values = list(all_styles)
        if selection_mode == "单选模式":
            values = values[-1:]
        if selection_mode in ("多选模式（逐一生成）", "全选模式"):
            values = list(dict.fromkeys(v for v in values if v in all_styles))
            pairs = [cls._combine(all_styles, [v], positive, negative) for v in values]
            return io.NodeOutput([p[0] for p in pairs], [p[1] for p in pairs],
                                 [cls._filename(filename_prefix, all_styles, [v]) for v in values])
        result = cls._combine(all_styles, values, positive, negative)
        return io.NodeOutput([result[0]], [result[1]], [cls._filename(filename_prefix, all_styles, values)])

    @staticmethod
    def _filename(prefix, all_styles, values):
        import re
        import hashlib
        from datetime import datetime
        now = datetime.now()
        tokens = {"yyyy": f"{now.year:04d}", "yy": f"{now.year % 100:02d}",
                  "MM": f"{now.month:02d}", "dd": f"{now.day:02d}",
                  "HH": f"{now.hour:02d}", "hh": f"{now.hour:02d}",
                  "mm": f"{now.minute:02d}", "ss": f"{now.second:02d}"}
        prefix = prefix or "Krea2-%date:yyyyMMddhhmmss%"
        prefix = re.sub(r"%date:([^%]+)%", lambda match: re.sub(
            r"yyyy|yy|MM|dd|HH|hh|mm|ss", lambda token: tokens[token[0]], match[1]), prefix)
        names = [str(all_styles[v].get('name_cn') or v) for v in values if v in all_styles]
        raw = '+'.join(names) or '无风格'
        safe = re.sub(r'[<>:"/\\|?*%\x00-\x1f]', '_', raw).strip(' .') or 'style'
        if safe != raw or len(safe) > 96:
            safe = safe[:80].rstrip(' .') + '_' + hashlib.sha256(raw.encode('utf-8')).hexdigest()[:8]
        return prefix + '_' + safe

    @staticmethod
    def _combine(all_styles, values, positive, negative):
        positive_prompt, negative_prompt = '', negative
        if not values:
            return positive, negative
        has_prompt = False

        for index, val in enumerate(values):
            if val not in all_styles:
                continue
            if 'prompt' in all_styles[val]:
                if "{prompt}" in all_styles[val]['prompt'] and has_prompt == False:
                    positive_prompt = all_styles[val]['prompt'].replace('{prompt}', positive)
                    has_prompt = True
                elif "{prompt}" in all_styles[val]['prompt']:
                    positive_prompt += ', ' + all_styles[val]['prompt'].replace(', {prompt}', '').replace('{prompt}', '')
                else:
                    positive_prompt = all_styles[val]['prompt'] if positive_prompt == '' else positive_prompt + ', ' + all_styles[val]['prompt']
            if 'negative_prompt' in all_styles[val]:
                negative_prompt += ', ' + all_styles[val]['negative_prompt'] if negative_prompt else all_styles[val]['negative_prompt']

        if has_prompt == False and positive:
            positive_prompt = positive + positive_prompt + ', '

        return positive_prompt, negative_prompt



class StyleSelectorExtension(ComfyExtension):
    async def get_node_list(self):
        return [StyleSelectorEnhancement]


async def comfy_entrypoint():
    return StyleSelectorExtension()

