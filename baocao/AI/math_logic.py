def try_math(sentence: str):
    try:
        result = eval(sentence)
        return f"Kết quả là: {result}"
    except:
        return None
