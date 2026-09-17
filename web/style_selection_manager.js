import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

const MODES = ["多选模式（叠加）", "单选模式", "多选模式（逐一生成）", "全选模式"];
const KEY = "styleSelectorEnhancement.favorites.v1";
const cache = new Map();
const instances = new Set();
const css = document.createElement("style");
css.textContent = `
.eu-style-panel,.eu-style-dialog{font:13px sans-serif;color:#eee;background:#24282d;box-sizing:border-box}
.eu-style-panel{padding:8px;overflow:auto;border:1px solid #58636d;border-radius:6px}
.eu-style-panel button,.eu-style-dialog button,.eu-style-dialog select,.eu-style-dialog input{font:inherit;color:#eee;background:#353e48;border:1px solid #64717c;border-radius:5px;padding:6px;cursor:pointer}
.eu-style-chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px;max-height:100px;overflow:auto}
.eu-style-chips button{font-size:12px;text-align:left}
.eu-style-dialog{width:min(1150px,94vw);height:85vh;border:1px solid #8294a4;border-radius:12px;padding:18px}
.eu-style-dialog::backdrop{background:#0009}
.eu-style-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.eu-style-columns{display:grid;grid-template-columns:2fr 1fr;gap:14px;height:calc(100% - 135px)}
.eu-style-cards{overflow:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:8px;align-content:start}
.eu-style-card{padding:7px;border:1px solid #53606c;border-radius:8px;display:flex;flex-direction:column;gap:6px}
.eu-style-card.active{border:2px solid #67d6ac;background:#21483d}
.eu-style-card img{width:100%;height:110px;object-fit:cover;background:#15191d}
.eu-style-card button{white-space:normal;overflow-wrap:anywhere}
.eu-style-side{overflow:auto;border-left:1px solid #53606c;padding-left:12px}
.eu-style-side .eu-style-chips{max-height:none}
.eu-style-status{min-height:24px;color:#aacdbf}
`;
document.head.append(css);

function el(tag, text, cls) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (cls) node.className = cls;
    return node;
}
function button(text, fn) {
    const b = el("button", text); b.type = "button"; b.onclick = fn; return b;
}
function favorites() {
    try { const v = JSON.parse(localStorage.getItem(KEY) || "[]"); return Array.isArray(v) ? v : []; }
    catch { return []; }
}
async function stylesFor(name) {
    if (!cache.has(name)) {
        const response = await api.fetchApi(`/style-selector-enhancement/styles?name=${encodeURIComponent(name)}`);
        if (!response.ok) throw new Error("风格库读取失败，请稍后重试");
        cache.set(name, await response.json());
    }
    return cache.get(name);
}
function attach(node) {
    if (node._styleManager) return;
    const widget = name => node.widgets?.find(w => w.name === name);
    if (!widget("select_styles") || !widget("selection_mode")) return;
    node._styleManager = true;
    const category = () => widget("styles").value;
    const selected = () => {
        const v = widget("select_styles").value;
        return Array.isArray(v) ? [...v] : (v ? String(v).split(",").filter(Boolean) : []);
    };
    const mode = () => widget("selection_mode").value;
    let library = [], loadedCategory = "", previous = [], signature = "", dialog = null;
    let renderDialog = null, status = null, loading = false;
    const panel = el("div", "", "eu-style-panel");
    const heading = el("div"); const chips = el("div", "", "eu-style-chips");
    const setSelected = names => {
        widget("select_styles").value = [...new Set(names)].join(",");
        app.graph?.setDirtyCanvas(true, true);
        refresh();
    };
    const label = name => library.find(s => s.name === name)?.name_cn || name;
    const report = text => { heading.textContent = text; if (status) status.textContent = text; };
    function refresh() {
        const names = selected();
        heading.textContent = `已选 ${names.length} 种 · ${mode()}（点 × 删除）`;
        chips.replaceChildren(...names.map(name => button(`${label(name)} ×`, () => setSelected(selected().filter(n => n !== name)))));
        previous = names;
        signature = JSON.stringify([category(), mode(), names]);
        renderDialog?.();
    }
    async function load() {
        const name = category();
        loading = true;
        try {
            const data = await stylesFor(name);
            if (category() !== name) return;
            const changed = loadedCategory && loadedCategory !== name;
            library = data; loadedCategory = name;
            if (changed) setSelected(mode() === "全选模式" ? library.map(s => s.name) : []);
            else refresh();
        } catch (e) { report(e.message); }
        finally { loading = false; }
    }
    async function changeMode(value) {
        widget("selection_mode").value = value;
        if (loadedCategory !== category()) await load();
        if (value === "全选模式") setSelected(library.map(s => s.name));
        else if (value === "单选模式") setSelected(selected().slice(-1));
        else refresh();
    }
    function toggle(name) {
        const names = selected();
        setSelected(names.includes(name) ? names.filter(n => n !== name) : mode() === "单选模式" ? [name] : [...names, name]);
    }
    function star(name) {
        const cat = category(); const f = favorites();
        const index = f.findIndex(s => s.category === cat && s.name === name);
        if (index < 0) f.push({category: cat, name}); else f.splice(index, 1);
        try { localStorage.setItem(KEY, JSON.stringify(f)); renderDialog?.(); }
        catch { report("收藏保存失败：浏览器本地存储不可用"); }
    }
    async function open() {
        if (dialog) { dialog.focus(); return; }
        await load();
        dialog = el("dialog", "", "eu-style-dialog");
        const title = el("h3", "风格选择与收藏"); title.style.marginTop = "0";
        const toolbar = el("div", "", "eu-style-toolbar");
        const modes = el("select"); MODES.forEach(m => { const o = el("option", m); o.value = m; modes.append(o); });
        modes.value = mode(); modes.onchange = () => changeMode(modes.value);
        const search = el("input"); search.placeholder = "搜索名称或提示词";
        const filter = el("select");
        [["all","当前分类"],["favorites","收藏夹（当前分类）"]].forEach(([v,t]) => {const o=el("option",t);o.value=v;filter.append(o);});
        toolbar.append(modes, search, filter, button("全选当前分类", () => changeMode("全选模式")), button("清空已选", () => setSelected([])), button("关闭", () => dialog.close()));
        status = el("div", "", "eu-style-status");
        const cols = el("div", "", "eu-style-columns"), cards = el("div", "", "eu-style-cards"), side = el("div", "", "eu-style-side");
        cols.append(cards, side); dialog.append(title, toolbar, status, cols);
        renderDialog = () => {
            const names = selected(), f = favorites(), cat = category();
            const starred = name => f.some(s => s.category === cat && s.name === name);
            const term = search.value.trim().toLowerCase();
            modes.value = mode();
            status.textContent = `${cat} · ${library.length} 种 · 已选 ${names.length} 种 · ${["全选模式","多选模式（逐一生成）"].includes(mode()) ? `输出 ${names.length} 条独立提示词` : "输出一条提示词"}`;
            const results = library.filter(s => (filter.value !== "favorites" || starred(s.name)) && `${s.name} ${s.name_cn || ""} ${s.prompt || ""}`.toLowerCase().includes(term));
            cards.replaceChildren(...results.map(s => {
                const card = el("div", "", `eu-style-card${names.includes(s.name) ? " active" : ""}`);
                const src = Array.isArray(s.thumbnail) ? s.thumbnail[0] : s.thumbnail;
                if (src) {const img=el("img");img.loading="lazy";img.src=src;img.alt=label(s.name);card.append(img);}
                card.append(button(`${names.includes(s.name) ? "✓ " : ""}${label(s.name)}`, () => toggle(s.name)), button(starred(s.name) ? "★ 取消收藏" : "☆ 收藏", () => star(s.name)));
                return card;
            }));
            const picked = el("div", "", "eu-style-chips");
            picked.append(...names.map(n => button(`${label(n)} ×`, () => setSelected(selected().filter(v => v !== n)))));
            side.replaceChildren(el("h4", `已选风格 · ${names.length}`), picked, el("p", "收藏保存在当前浏览器，跨工作流共享；切换原节点的风格类型可查看其他分类收藏。"));
        };
        search.oninput = renderDialog; filter.onchange = renderDialog;
        dialog.onclose = () => {dialog.remove();dialog=null;renderDialog=null;status=null;};
        document.body.append(dialog); renderDialog(); dialog.showModal();
    }
    panel.append(button("管理风格 / 收藏夹", open), heading, chips);
    node.addDOMWidget("style_selection_manager", "STYLE_MANAGER", panel, {serialize: false, getMinHeight: () => 100, getMaxHeight: () => 145});
    const modeWidget = widget("selection_mode"); const oldChange = modeWidget.callback;
    modeWidget.callback = function(value) {oldChange?.apply(this, arguments);changeMode(value);};
    const state = {tick() {
        if (!node.graph) return;
        if (loadedCategory !== category() && !loading) {load();return;}
        const names = selected();
        if (mode() === "单选模式" && names.length > 1) {
            setSelected([names.find(n => !previous.includes(n)) || names.at(-1)]);return;
        }
        if (JSON.stringify([category(),mode(),names]) !== signature) refresh();
    }};
    instances.add(state);
    const removed = node.onRemoved;
    node.onRemoved = function() {instances.delete(state);dialog?.close();return removed?.apply(this, arguments);};
    load();
}
setInterval(() => instances.forEach(s => s.tick()), 400);
app.registerExtension({
    name: "StyleSelectorEnhancement.Manager",
    nodeCreated(node) {if (node.comfyClass === "StyleSelectorEnhancement" || node.type === "StyleSelectorEnhancement") setTimeout(() => attach(node), 0);},
    loadedGraphNode(node) {if (node.type === "StyleSelectorEnhancement") setTimeout(() => attach(node), 0);}
});
