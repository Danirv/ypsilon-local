# Ypsilon 2.4.0

Local Home Assistant integration for compatible Runxin F79D / BroadLink BL3372 water softeners, tested with ATH/BWT Ypsilon G6.

## 2.4.0

This release keeps the Home Assistant behavior of 2.3.x while restructuring the reverse-engineered protocol work so it can be reused safely by future transports and Runxin device profiles:

- transport-neutral, Home-Assistant-independent `runxin/` package;
- declarative F79D field catalogue with conservative evidence/provenance metadata;
- isolated BroadLink BL3372 transport (`0x6A`, authentication, encryption, TFB framing, retries and session handling);
- compatibility facades for the previous `api.py` / `protocol.py` imports;
- architecture, protocol, F79D, BL3372, new-transport and new-device-profile documentation;
- expanded offline regression checks that pin the existing wire encoding and enforce layer boundaries.

There are no intentional entity, config-entry, unique-id, polling or write-verification changes. The Home Assistant integration still supports the verified F79D + BL3372/Ypsilon combination; the reusable protocol layer does not imply automatic support for every Runxin controller or transport.
