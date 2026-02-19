from CAIR import Analyze

model = Analyze(
    model_name="gpt-5-mini",
    reasoning_effort="low",
    websearch=True,
)

result = model(
    prompt="Name one recent U.S. AI policy development and include one source URL.",
    system_prompt="You are a concise policy analyst. Keep output to 3 bullets.",
)

print(result)
print(model.usage)
