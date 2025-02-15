from typing import Optional

class Magic:
    def __init__(self, mime: bool = False, magic_file: Optional[str] = None, keep_going: bool = False) -> None: ...
    def from_file(self, filename: str) -> str: ...
    def from_buffer(self, buffer: bytes) -> str: ...
    def close(self) -> None: ... 