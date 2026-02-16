import re


def build_page_map(segmenty):
    page_map = {}
    for seg in segmenty:
        page = seg.get("page")
        text = seg.get("text", "")
        if page is not None:
            page_map[page] = text
    return page_map


def parse_pages(citovane_zdroje):
    pages = set()

    if isinstance(citovane_zdroje, list):
        for it in citovane_zdroje:
            if isinstance(it, int):
                pages.add(it)
            elif isinstance(it, str):
                for token in re.split(r"[,\s/]+", it):
                    token = token.strip()
                    if token.isdigit():
                        pages.add(int(token))
    elif isinstance(citovane_zdroje, (int, float)):
        pages.add(int(citovane_zdroje))
    elif isinstance(citovane_zdroje, str):
        for token in re.split(r"[,\s/]+", citovane_zdroje):
            token = token.strip()
            if token.isdigit():
                pages.add(int(token))

    return sorted(pages)


def build_context_for_lo(lo, page_map, max_chars=8000):
    cit = lo.get("citovane_zdroje", [])
    pages = parse_pages(cit)
    if not pages:
        return ""

    texts = []
    total_len = 0
    for p in pages:
        txt = page_map.get(p, "")
        if not txt:
            continue
        if total_len + len(txt) > max_chars:
            remaining = max_chars - total_len
            if remaining > 200:
                texts.append(txt[:remaining])
                total_len += remaining
            break
        else:
            texts.append(txt)
            total_len += len(txt)

    return "\n\n".join(texts)
