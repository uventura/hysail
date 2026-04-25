_IS_DEBUGGING = False

def set_debugging(value: bool):
    global _IS_DEBUGGING
    _IS_DEBUGGING = value

def is_debugging() -> bool:
    return _IS_DEBUGGING

