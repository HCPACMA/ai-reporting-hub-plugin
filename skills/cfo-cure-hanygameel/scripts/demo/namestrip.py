import re
AR = r'[ء-ي]+'
HON = re.compile(r'(?:(?<=[\s(])|^)(?:(?:د|ا|أ|م|ل|لد)\s?[/.]\s*|(?:الدكتور|الدكتورة|دكتور|دكتورة|الموظف|الموظفة|السيد|السيدة|الاخ|الأخ|الاخت|الأخت|الشيخ|للشيخ|المهندس)\s*[/.]?\s*)(' + AR + r'(?:\s+' + AR + r'){0,2})')
EN = re.compile(r'\b(?:Dr|DR|Mr|Mrs|Ms)\.?\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})')
GENERIC = {'شهر','عن','من','الى','إلى','حتى','بتاريخ','سنة','لشهر','مبلغ','قيمة','فاتورة','رقم'}
def strip(s, A, role='person'):
    if not isinstance(s, str): return s
    def ar(m):
        words = m.group(1).split()
        keep = []
        for w in words:
            if w in GENERIC: break
            keep.append(w)
        if not keep: return m.group(0)
        name = ' '.join(keep)
        rest = m.group(1)[len(name):]
        pre = m.group(0)[:m.start(1)-m.start(0)]
        return pre + A.person(name, role) + rest
    s = HON.sub(ar, s)
    s = EN.sub(lambda m: m.group(0)[:m.start(1)-m.start(0)] + A.person(m.group(1), role), s)
    return s
