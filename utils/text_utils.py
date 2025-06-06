# utils/text_utils.py

def reemplazar_caracteres(texto):
    mapeo_caracteres = {
        "Ã": "Á",
        "Ã‰": "É",
        "Ã": "Í",
        "Ã“": "Ó",
        "Ãš": "Ú",
        "Ã±": "ñ",
        "Ã‘": "Ñ",
        "Âª": "°",
        "Â°": "°"
    }
    if not isinstance(texto, str):
        return texto
    for mal, bien in mapeo_caracteres.items():
        texto = texto.replace(mal, bien)
    return texto
