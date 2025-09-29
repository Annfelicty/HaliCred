import importlib.util

spec = importlib.util.find_spec("dotenv")
print({"found": spec is not None})
