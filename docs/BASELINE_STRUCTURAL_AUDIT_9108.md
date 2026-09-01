# FX 9.1.0.8 structural audit

This audit is taken from the untouched canonical 9.1.0.8 APK, SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`.

It exists to prevent broad binary edits based on assumptions. Counts below come from parsing DEX tables and binary Android XML directly.

## DEX inventory

The APK contains one `classes.dex` with:

- 47,756 string IDs
- 14,071 type IDs
- 29,815 field IDs
- 55,769 method IDs
- 12,079 class definitions

Notable implementation groups in the untouched base:

- 231 class definitions under the legacy extended-module namespace.
- 173 class definitions belonging to the old store client/runtime family.
- 32 app-owned class definitions belonging to the old store-integration family.
- 182 class definitions under the Google Play-services namespace.
- 4 class definitions belonging to Google DataTransport runtime/CCT registration.
- 0 class definitions matching Firebase Analytics or Google measurement implementation namespaces.

The absence of Firebase Analytics/Measurement classes means those systems must not be claimed to exist merely because other Google libraries are present.

## Developer preferences

Binary preference resource `res/k_.xml` contains four checkbox entries in the untouched base:

1. `developerOptions`
2. `developerTV`
3. the legacy store-disable preference
4. `storageSandbox`

The legacy store-disable checkbox must be physically removed from this XML in FX Extended, together with its key, title, summary, read/write code and callers.

## Manifest inventory

The untouched manifest includes, among other normal FX components:

- the old store permission;
- module/catalog/interaction metadata for the legacy extended UI;
- the old status/update activity;
- two old store proxy activities;
- a Google common API activity;
- Google runtime version metadata;
- DataTransport backend discovery service;
- DataTransport job-scheduler service;
- DataTransport alarm receiver;
- CCT backend metadata.

These entries must be evaluated by surviving call graph, not simply hidden.

## DataTransport call-path finding

A DEX call-reference pass found the CCT backend factory reached through an obfuscated backend-registry method. That registry is reached from code that also calls the old store runtime.

A separate optimized/synthetic `Runnable.run()` contains many unrelated FX operations and one branch that reaches the same backend registry. This is important: the optimized APK has mixed responsibilities in some synthetic methods. Deleting an entire obfuscated/synthetic class merely because one branch belongs to removed infrastructure can break unrelated file-manager behavior.

Therefore removal must use a proper disassemble/edit/reassemble process with method- and branch-level reasoning where needed.

## Endpoint inventory

The untouched DEX contains approximately 90 HTTP/HTTPS-looking strings. Many are documentation/legal/library strings rather than live endpoints. Live-looking functional endpoints include:

- Google OAuth and Drive API endpoints;
- Microsoft OAuth and Graph/OneDrive endpoints;
- Box API/OAuth/upload endpoints;
- SugarSync API endpoints;
- NextApp-hosted theme/BusyBox/redirect endpoints;
- local Web Access loopback endpoints.

Network minimization requires tracing callers before deletion. Explicit cloud/network file operations should continue to work. Promotional/update/telemetry/background-only endpoints should be removed with their callers.

## Network/telemetry rule

Every surviving outbound network path must have a documented, user-initiated file-manager purpose. No analytics, measurement, attribution, telemetry upload, crash upload, remote promotion, background diagnostics, unsolicited update check or background ping is allowed in the finished FX Extended build.

## Verification implication

The next build must produce a before/after structural report for:

- class definitions;
- methods and fields;
- manifest components;
- preference entries;
- resource records;
- endpoint strings and callers;
- startup initializers;
- DataTransport/Google components;
- removed legacy subsystem artifacts.

A zero-hit printable-string scan is useful as a final check, but it is not sufficient proof of deletion.