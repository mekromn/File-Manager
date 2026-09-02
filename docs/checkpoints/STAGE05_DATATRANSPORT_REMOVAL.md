# Stage 05 — telemetry/DataTransport structural removal

Source checkpoint: verified Stage 04 tree.

Transformations:

- `tools/stages/stage05a_sever_logging_transport.py`
- `tools/stages/stage05b_prune_unreachable_shaded.py`
- `tools/stages/stage05c_remove_transport_runtime.py`
- `tools/stages/stage05d_remove_transport_backend.py`
- `tools/stages/stage05e_strip_eventstore_bridges.py`
- `tools/stages/stage05f_strip_last_transport_mixed.py`
- `tools/stages/stage05g_prune_datatransport_graph.py`

## Structural work completed

- Physically removed the uncalled BillingLogger-to-transport send root and its event-envelope/encoder path.
- Recomputed reachability for the shaded generated runtime and physically deleted 56 classes that had no external root or transitive path from surviving code.
- Removed DataTransport Android scheduler/discovery components from the manifest.
- Removed JobScheduler/AlarmManager runtime singleton/component/provider roots and only the transport-specific methods/branches from R8-shared classes.
- Removed backend discovery/registry/CCT factory roots.
- Removed event-store, transport-context, scheduler and work-initializer provider methods from mixed classes.
- Removed the final CCT/event encoder special-case methods/branches embedded in shared classes.
- Proved a 45-class DataTransport-only graph had zero external roots and physically deleted it as a unit.

## Final Stage 05 checkpoint

Unsigned APK:

- path used for verification: `stage05g-unsigned.apk`
- size: 12,943,018 bytes
- SHA-256: `0ebd351fa60422c3e1ea7a670754ea8c12e8ef49c92b59d8034c5f34b1481086`
- Apktool rebuild: success
- ZIP integrity: success

Independent rebuilt-DEX verification with pinned baksmali 3.0.10:

- class files: 11,895
- DataTransport namespace class files: 0
- old app-owned IAB descriptor references: 0
- public BillingClient API descriptor references: 0
- manifest DataTransport component references: 0
- DataTransport/CCT/event-store marker hits (`SQLiteEventStore`, `transport_contexts`, `log_event_dropped`, `CctTransportBackend`, DataTransport user-agent/event namespace): 0

## Shaded generated-runtime boundary

After the transport/telemetry deletion, `com.google.android.gms.internal.play_billing` contains 111 classes.

A fresh reachability pass finds:

- total shaded classes: 111
- external roots: 13
- transitively reachable: 111
- unreachable: 0

The roots include generic/shared helpers used by normal file-manager code (for example callback/progress, stream/collection/backport and other R8-shared utility paths). Therefore Stage 05 deliberately does **not** delete those 111 classes by package name.

Their legacy package name is not accepted as final DW naming. The next neutral-namespace stage will migrate the surviving shared runtime to a neutral DW runtime namespace through a real smali rebuild, while preserving only classes that remain reachable.

## Deliberately pending

Stage 05 does not yet claim completion of:

- neutral migration of the 111 surviving shaded generated classes;
- full `nextapp.*` -> `dw.filemanager.*` app-owned namespace migration;
- useful former extended-module `plus` namespace/class/resource renaming;
- four-ABI JNI bridge migration for `NativeFileAccess`;
- Google common/Drive OAuth runtime reachability audit;
- app-owned EULA/vendor branding/legal/help cleanup;
- drawer-body theme hook;
- adaptive DW icon replacement;
- final signing/device regression testing.

No user-test APK is produced by this checkpoint.
