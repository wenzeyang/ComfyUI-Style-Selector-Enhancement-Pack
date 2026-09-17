class stylesPromptSelector(io.ComfyNode):

    @classmethod
    def define_schema(cls):
        styles = ["fooocus_styles"]
        styles_dir = FOOOCUS_STYLES_DIR
        for file_name in os.listdir(styles_dir):
            file = os.path.join(styles_dir, file_name)
            if os.path.isfile(file) and file_name.endswith(".json"):
                if file_name != "fooocus_styles.json":
                    styles.append(file_name.split(".")[0])

        return io.Schema(
            node_id="easy stylesSelector",
            category="EasyUse/Prompt",
            inputs=[
                io.Combo.Input("styles", options=styles, default="fooocus_styles"),
                io.String.Input("positive", default="", force_input=True, optional=True),
                io.String.Input("negative", default="", force_input=True, optional=True),
                io.Custom(io_type="EASY_PROMPT_STYLES").Input("select_styles", optional=True),
                io.Combo.Input("selection_mode", options=["多选模式（叠加）", "单选模式", "多选模式（逐一生成）", "全选模式"], default="多选模式（叠加）", optional=True),
            ],
            outputs=[
                io.String.Output(id="output_positive", display_name="positive", is_output_list=True),
                io.String.Output(id="output_negative", display_name="negative", is_output_list=True),
            ],
            hidden=[
                io.Hidden.prompt,
                io.Hidden.extra_pnginfo,
                io.Hidden.unique_id,
            ],
        )

    @classmethod
    def execute(cls, styles, positive='', negative='', select_styles=None, selection_mode="多选模式（叠加）", **kwargs):
        values = []
        all_styles = {}
        positive_prompt, negative_prompt = '', negative
        fooocus_custom_dir = os.path.join(FOOOCUS_STYLES_DIR, 'fooocus_styles.json')
        if styles == "fooocus_styles" and not os.path.exists(fooocus_custom_dir):
            file = os.path.join(RESOURCES_DIR,  styles + '.json')
        else:
            file = os.path.join(FOOOCUS_STYLES_DIR, styles + '.json')
        f = open(file, 'r', encoding='utf-8')
        data = json.load(f)
        f.close()
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
            return io.NodeOutput([p[0] for p in pairs], [p[1] for p in pairs])
        result = cls._combine(all_styles, values, positive, negative)
        return io.NodeOutput([result[0]], [result[1]])

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

