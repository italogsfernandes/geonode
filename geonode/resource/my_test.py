class MyContextManager(object):
    def __init__(self):
        self.requests = []
        print("MyContextManager __init__")

    def __enter__(self):
        print("MyContextManager __enter__")

        return self
    def __exit__(self, exc_type, exc_value, exc_tb):
        print(f"MyContextManager __exit__(exc_type={exc_type}, exc_value={exc_value}, exc_tb={exc_tb})")

    def say_hello(self):
        print("hello")

    def add_request(self, request):
        self.requests.append(request)


print("ctx_manager = MyContextManager()")
ctx_manager = MyContextManager()
print("with ctx_manager:")
with ctx_manager:
    print("ctx_manager.say_hello()")
    ctx_manager.say_hello()
    print("ctx_manager.add_request('surprise')")
    ctx_manager.add_request('surprise')
    print("with ctx_manager as ctx_manager2:")
    print(ctx_manager.requests)
    with ctx_manager as ctx_manager2:
        print("ctx_manager2.say_hello()")
        ctx_manager2.say_hello()
        print("ctx_manager2.add_request('motherfucker')")
        ctx_manager2.add_request('motherfucker')
        print(ctx_manager2.requests)
        print(ctx_manager.requests)
    print("doing something else")
    