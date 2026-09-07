# Adding another transport

The reusable F79D client consumes a deliberately small structural interface:

```python
class MyTransport:
    def transact(self, frame: bytes) -> bytes:
        """Send one raw Runxin frame and return one raw Runxin frame."""
        ...
```

Optional hooks are recognised when present:

```python
class MyTransport:
    def transact(self, frame: bytes) -> bytes: ...
    def invalidate(self) -> None: ...  # reset session/framing after bad reply
    def close(self) -> None: ...       # release resources
```

The client can then be used without Home Assistant:

```python
from runxin.client import F79DClient

client = F79DClient(MyTransport(...))
identity = client.read_identity()
state = client.read_state()
client.write_fields({43: 50})
```

When experimenting outside this repository, vendor/copy the pure `runxin/`
package or use it from a source checkout. Do not create a Home Assistant custom
integration that imports another installed custom integration at runtime.

## What `transact()` must return

Return the **raw Runxin frame**, starting with `5A 5C`. Do not return:

- a BroadLink encrypted packet;
- the BL3372 TFB length prefix;
- serial/TCP framing bytes belonging only to your adapter;
- already decoded dictionaries.

Your transport is responsible for removing its own envelope before handing the
response to `F79DClient`.

## Examples of future transports

Potential transports include direct UART/serial, TCP bridges, ESPHome-backed
links or another vendor Wi-Fi module. None are supported until tested.

A new transport should live under `transport/` and should ideally subclass
`RunxinTransport` from `transport/base.py`. The F79D client uses structural
typing, so subclassing is convenient but not mandatory.

## Tests required for a contribution

Add offline tests to `scripts/audit.py` that prove at least:

1. the transport sends the exact raw Runxin request unchanged;
2. its envelope is added/removed only in the transport layer;
3. malformed/truncated responses fail closed;
4. session reset/retry behavior is bounded;
5. `runxin/` remains free of transport-specific imports.

Real-hardware validation should be documented separately from simulated tests.
Do not enable automatic discovery for a new hardware family until its identity
and false-positive behavior are understood.
