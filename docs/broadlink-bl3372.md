# BroadLink BL3372 transport

`transport/broadlink_bl3372.py` is the concrete transport used by the Home
Assistant integration today. It is intentionally separate from the F79D codec.

## Tested combination

- BroadLink device type: `0x520F`
- module family: BL3372
- product controller: Runxin F79D
- BroadLink command carrying product data: `0x6A`
- Python dependency: `broadlink==0.19.0`

The Home Assistant integration still probes for the tested device type/model.
The transport class is parameterised so research code can test a different
BroadLink devtype without changing the Runxin codec, but that does not make the
new combination supported by Ypsilon.

## Transaction path

```text
raw Runxin request
 -> prepend uint16-le payload length (TFB)
 -> BroadLink send_packet(0x6A, ...)
 -> validate outer BroadLink response
 -> decrypt response body
 -> remove TFB length/padding
 -> raw Runxin response
```

The transport returns the raw Runxin response. It never decodes F79D fields.

## Session handling

The transport keeps one authenticated BroadLink session and reuses it. It
serializes transactions because the device path is stateful and because the
underlying module/controller link should not receive overlapping requests.

Observed outer response behavior:

- `-1` / `-7`: treated as stale authentication/session failures; one fresh auth
  is attempted;
- `-5`: treated as a short-lived retryable condition on the tested hardware;
  retries use the same session with short jittered delays.

Older project comments attributed `-5` to a specific MCU/cloud UART condition.
That causal explanation is **not proven** by the available captures. v2.4 keeps
the empirically useful retry policy while documenting only what is supported by
evidence: the error is transient on this device and often clears on retry.

A final transport/protocol failure invalidates the session so the next poll can
start from a clean authentication state.

## Diagnostics

The transport exposes counters for:

- transient retries;
- re-authentication attempts;
- BroadLink firmware version when readable.

The Ypsilon adapter maps these into the existing Home Assistant diagnostics, so
v2.4 does not change entity identities or dashboard behavior.

## Replacing BroadLink

A different transport does not need to emulate BroadLink. It only needs to
accept a raw Runxin request and return a raw Runxin response. TFB, `0x6A`,
BroadLink encryption and outer errors must not leak into the new transport's
public contract.

See `adding-a-transport.md`.
