def clean_code(content):
    content = content.replace("\n", " ", 1)
    i = content.find(" ")
    j = content.rfind("```")
    if i > 0 and j > 0:
        code = content[i:j]
    else:
        code = content
    return code
