
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, Optional, Protocol, runtime_checkable, Self

logger = logging.getLogger(__name__)


@runtime_checkable
class OutputStream(Protocol):
    async def write(
            self,
            *objects: Any,
            sep: str | None = None,
            end: str | None = None,
            flush: bool = False
    ) -> None:
        """Print data to the output stream."""


@runtime_checkable
class InputStream(Protocol):
    async def read(
            self,
            prompt: str | None = None,
            *,
            password: bool = False
    ) -> str:
        """Read a line from the input stream."""


@runtime_checkable
class IOStream(InputStream, OutputStream, Protocol):
    """A protocol for input/output streams."""

    _default_io_stream: ContextVar[Self | None] = ContextVar("default_iostream", default=None)
    _global_default: Self | None = None

    @staticmethod
    def set_global_io_stream(stream: "IOStream") -> None:
        """Set the global default IO stream."""
        IOStream._global_default = stream

    @staticmethod
    def get_global_io_stream() -> "IOStream":
        """Get the global default IO stream."""
        if IOStream._global_default is None:
            raise RuntimeError("No global default IOStream has been set.")
        return IOStream._global_default

    @staticmethod
    def get_current_io_stream() -> "IOStream":
        """Get the current context's default IO stream."""
        iostream = IOStream._default_io_stream.get()
        if iostream is None:
            iostream = IOStream.get_global_io_stream()
            IOStream.override_default_io_stream(iostream)
        return iostream

    @staticmethod
    @contextmanager
    async def override_default_io_stream(stream: Optional["IOStream"]) -> Iterator[None]:
        """Temporarily override the default IO stream for the current context."""
        token = IOStream._default_io_stream.set(stream)
        try:
            yield
        finally:
            IOStream._default_io_stream.reset(token)
