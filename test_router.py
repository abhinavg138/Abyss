from assistant.router import Router

router = Router()

messages = [

    {

        "role":"user",

        "content":"What is 2+2?"

    }

]

print(router.chat(messages))