import re


SOURCE_REF_RE = re.compile(r"\b([A-Za-z]\w*)\s*[:#-]\s*(\d+)\b")


def get_segment_source_id(seg):
    source_id = str(seg.get("source_id") or "").strip()
    return source_id.upper() or None


def get_segment_source_name(seg):
    return str(seg.get("source_name") or "").strip()


def make_source_ref(source_id, page):
    if source_id:
        return f"{str(source_id).strip().upper()}:{page}"
    return str(page)


def format_segment_label(seg):
    page = seg.get("page")
    source_id = get_segment_source_id(seg)
    source_name = get_segment_source_name(seg)
    if source_id and source_name:
        return f"dokument {source_id} ({source_name}), strana {page}"
    if source_id:
        return f"dokument {source_id}, strana {page}"
    return f"strana {page}"


def build_page_map(segmenty):
    page_map = {}
    for seg in segmenty:
        page = seg.get("page")
        text = seg.get("text", "")
        if page is not None:
            source_id = get_segment_source_id(seg)
            source_ref = make_source_ref(source_id, page)
            page_map[source_ref] = text
            page_map[(source_id, int(page))] = text
            if not source_id:
                page_map[int(page)] = text
            page_map.setdefault(int(page), text)
    return page_map


def iter_source_values(citovane_zdroje):
    if isinstance(citovane_zdroje, list):
        values = citovane_zdroje
    elif citovane_zdroje is None:
        values = []
    else:
        values = [citovane_zdroje]

    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            yield str(int(value))
        else:
            text = str(value).strip()
            if text:
                yield text


def parse_source_refs(citovane_zdroje):
    refs = []
    seen = set()

    for text in iter_source_values(citovane_zdroje):
        matched = False
        for source_id, page_text in SOURCE_REF_RE.findall(text):
            matched = True
            ref = (source_id.strip().upper(), int(page_text))
            if ref not in seen:
                refs.append(ref)
                seen.add(ref)

        if matched:
            continue

        for token in re.split(r"[,\s/]+", text):
            token = token.strip()
            if token.isdigit():
                ref = (None, int(token))
                if ref not in seen:
                    refs.append(ref)
                    seen.add(ref)

    return refs


def parse_pages(citovane_zdroje):
    pages = set()
    for _, page in parse_source_refs(citovane_zdroje):
        pages.add(page)
    return sorted(pages)


def parse_source_ref_strings(citovane_zdroje):
    refs = []
    for source_id, page in parse_source_refs(citovane_zdroje):
        refs.append(make_source_ref(source_id, page))
    return refs


def build_allowed_source_refs(segmenty):
    refs = set()
    source_ids = {
        get_segment_source_id(seg)
        for seg in segmenty
        if seg.get("page") is not None
    }
    single_source = len(source_ids) <= 1
    for seg in segmenty:
        page = seg.get("page")
        if page is None:
            continue
        source_id = get_segment_source_id(seg)
        refs.add(make_source_ref(source_id, int(page)))
        if single_source:
            refs.add(str(int(page)))
    return refs


def build_source_name_map(segmenty):
    source_names = {}
    first_name = ""
    for seg in segmenty:
        source_id = get_segment_source_id(seg)
        source_name = get_segment_source_name(seg)
        if source_name and not first_name:
            first_name = source_name
        if source_id and source_name:
            source_names[source_id] = source_name

    if first_name:
        source_names[None] = first_name
    return source_names


def resolve_source_names(citovane_zdroje, source_name_map):
    names = []
    seen = set()
    for source_id, _ in parse_source_refs(citovane_zdroje):
        name = source_name_map.get(source_id)
        if not name and source_id is None:
            name = source_name_map.get(None)
        if not name:
            name = source_id or ""
        if name and name not in seen:
            names.append(name)
            seen.add(name)
    return names


def build_context_for_sources(citovane_zdroje, page_map, max_chars=8000):
    refs = parse_source_refs(citovane_zdroje)
    if not refs:
        return ""

    texts = []
    total_len = 0
    for source_id, page in refs:
        txt = (
            page_map.get((source_id, page))
            or page_map.get(make_source_ref(source_id, page))
            or page_map.get(page)
            or ""
        )
        if not txt:
            continue
        if total_len + len(txt) > max_chars:
            remaining = max_chars - total_len
            if remaining > 200:
                texts.append(txt[:remaining])
                total_len += remaining
            break
        texts.append(txt)
        total_len += len(txt)

    return "\n\n".join(texts)


def build_context_for_lo(lo, page_map, max_chars=8000):
    return build_context_for_sources(lo.get("citovane_zdroje", []), page_map, max_chars=max_chars)
