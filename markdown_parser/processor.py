from dataclasses import dataclass
from typing import Generic, Type, TypeVar
from markdown_parser.nodes import Node
from markdown_parser.lifter import HTMLNode

T = TypeVar("T", bound=Node)
U = TypeVar("U", bound=Node)
@dataclass
class Processor(Generic[T, U]):
    item_type: Type[T]

    @staticmethod
    def transform(node: T) -> list[U]:
        ...
    @staticmethod
    def render(node: U) -> list[HTMLNode]:
        ...

