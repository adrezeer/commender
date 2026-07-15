def register(register_command):
    def hello(args, raw_cmd):
        name = args[0] if args else "there"
        print(f"Hello, {name}! (from sample plugin)")

    register_command("hello", hello, "Say hello from plugin")
