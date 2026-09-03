import re

def normalize_column_name(name):
    if name is None:
        return ""
    name = str(name).strip().lower()
    name = name.replace("%", "percent")
    # Replace anything not a-z, 0-9 with underscore
    name = re.sub(r'[^a-z0-9]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

print(normalize_column_name("WVTR (∆W/(txA)) g/m²∙24 jam"))
