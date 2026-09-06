# Changelog (thw fork)

## 0.7.4 - 2026-09-06
- Requires smartrent-py 0.7.4 (fresh connection for every send).

## 0.7.3 - 2026-09-05
- Requires smartrent-py 0.7.3. Latency sensor gains a `verified` attribute:
  True when the lock's own operation notification confirmed the move, False
  when the hub reported a state the lock never acted on.

## 0.7.2 - 2026-09-05
- Requires smartrent-py 0.7.2 (commands sent over the live websocket).

## 0.7.1 - 2026-09-05
- Requires smartrent-py 0.7.1 (5/10/17 s re-send schedule, 25 s deadline).

## 0.7.0 - 2026-09-05
- Requires smartrent-py 0.7.0 (hub-confirmed commands).
- Lock reports `locking` / `unlocking` while the hub works and raises a
  `HomeAssistantError` when the hub never reports, so the service call and
  automation trace show the failure.
- Diagnostic sensor `<lock> command latency` (seconds to hub confirmation,
  attributes outcome / attempts / attribute / value / started / error).

## 0.6.1 - 2026-09-04
- Requires smartrent-py 0.6.1.

## 0.6.0 - 2026-08-29 (thw-fixes)
- Entities go unavailable when the cloud poll fails or the device is offline;
  string unique ids (registry migrated); no bogus lock OPEN feature.
