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
            ],
            outputs=[
                io.String.Output(id="output_positive", display_name="positive"),
                io.String.Output(id="output_negative", display_name="negative"),
            ],
            hidden=[
                io.Hidden.prompt,
                io.Hidden.extra_pnginfo,
                io.Hidden.unique_id,
            ],
        )

    @classmethod
    def execute(cls, styles, positive='', negative='', select_styles=None, **kwargs):
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
        # if my_unique_id in prompt:
        #     if prompt[my_unique_id]["inputs"]['select_styles']:
        #         values = prompt[my_unique_id]["inputs"]['select_styles'].split(',')

        if isinstance(select_styles, str):
            values = select_styles.split(',')
        else:
            values = select_styles if select_styles else []

        has_prompt = False
        if len(values) == 0:
            return io.NodeOutput(positive, negative)

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

        return io.NodeOutput(positive_prompt, negative_prompt)

