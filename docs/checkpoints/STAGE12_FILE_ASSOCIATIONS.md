# Stage 12 — File Type Associations

On-device validated baseline: **DW File Manager 9.1.0.8, versionCode 9109005**.

## Confirmed behavior

- File associations are keyed by exact file extension rather than broad MIME family.
- Normal file taps preserve the Stage 11 / v9109004 behavior when no preferred application has been configured.
- The existing DW **Open With** UI remains the explicit override path.
- Tapping an application in Open With opens once.
- Long-pressing an external application in Open With stores it as the preferred application for that exact file extension.
- Long-pressing the currently preferred application again clears the association.
- Once stored, a normal one-tap file open bypasses the chooser and routes through DW's existing Open With/retrieve/stream machinery to the stored component.
- Built-in DW viewers can therefore be overridden per extension without duplicating local/remote file handling.
- Stale or missing preferred components fall back to the existing DW open path rather than blocking file access.

## Persistence

Associations are stored in app preferences under the `dw.fileassoc.` namespace. No cloud/network state is involved.

## Non-regression baseline

This stage is built on the on-device-confirmed Stage 11 v9109004 baseline and retains:

- one app-wide companion package check only;
- normal/default former companion branches;
- the Settings ART verifier repair;
- AppDetailsActivity namespace target repair;
- the compiler-built four-ABI `libnative-file-access.so` JNI bridge with valid dynamic symbol/hash metadata;
- confirmed working Settings, Recent, images, videos, Apps submenus, and Cleaning Tools.

## Device result

The v9109005 file-association build was reported working on-device on 2026-09-02. This is the new feature baseline for subsequent document-picker sorting work.
