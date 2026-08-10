from assistant.manager import AssistantManager

assistant = AssistantManager()

print("Welcome to Abyss!")
print("Type 'exit' to quit.\n")

while True:

    query = input("You > ")

    if query.lower() == "exit":
        break

    print("Abyss >", end=" ", flush=True)

    for token in assistant.stream(query):
        print(token, end="", flush=True)

    print()