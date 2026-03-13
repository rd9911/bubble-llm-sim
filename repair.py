with open("tests/unit/prompts/test_render.py", "r") as f:
    code = f.read()

target = 'profile = TraderProfile(\n        reasoning_style="qre_like",'
replacement = 'profile = TraderProfile(\n        trader_id="test_trader",\n        run_id="test_run",\n        generation=0,\n        reasoning_style="qre_like",'
code = code.replace(target, replacement)

with open("tests/unit/prompts/test_render.py", "w") as f:
    f.write(code)

with open("src/bubble_sim/prompts/templates.py", "r") as f:
    text = f.read()

text = text.replace('"short reason"\\n}', '"short reason"\\n}}')
text = text.replace('"short reason"\\n}}', '"short reason"\\n}}')
text = text.replace('{\n  "action"', '{{\n  "action"')
text = text.replace('{{\n  "action"', '{{\n  "action"')
text = text.replace('}\\"""', '}}\\"""')

with open("src/bubble_sim/prompts/templates.py", "w") as f:
    f.write(text)
