# DW File Manager core rework requirements

The next accepted DW File Manager build must start from the immutable upstream 9.1.0.8 APK (SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`). Rejected test APKs are never build inputs.

## Product identity

The rebuilt application is **DW File Manager**.

- Application ID: `com.mekromn.dwfilemanager`
- User-facing label: `DW File Manager`
- Surviving app-owned Java/smali namespaces must be migrated away from the upstream vendor namespace to neutral `dw.filemanager.*`-style namespaces through a real DEX rebuild.
- App-owned intent actions, provider authorities, task affinities, preferences, resource identifiers, serialized class names and reflection strings must be migrated consistently.
- Upstream vendor branding, logos, names, promotional graphics and app-owned legal/promotional surfaces must not remain in normal UI, resources or surviving app-owned implementation symbols.
- The app icon must be replaced with a new DW File Manager adaptive icon. The intended visual direction is a clean, modern dark file/folder mark with a restrained DW monogram and Pixel blue `#4285F4` accent, avoiding the upstream logo.

The only tolerated upstream identity is compatibility data strictly necessary to identify the user's external companion package. It must be confined to the single companion helper/manifest visibility mechanism, must never be displayed, and must not become an internal namespace or branding dependency. If Android package visibility allows the external identifier to be constructed privately at runtime rather than stored as a plain-text app-owned string, prefer that representation.

## Structural deletion, not deactivation

Legacy state/store/time-window code that is no longer part of DW File Manager must be physically removed from the rebuilt DEX/resources. Making a branch unreachable, returning a constant, unregistering a screen while leaving its class, or renaming the old implementation does not count as removal.

The audit must inventory and resolve all related:

- classes and interfaces;
- methods and fields;
- activities, fragments, dialogs, services, receivers, providers, workers and schedulers;
- timers, callbacks, adapters, state models and enums;
- manifest declarations, permissions, queries, metadata and intent filters;
- preference XML entries and preference keys;
- layouts, menus, drawables, arrays, strings, plurals, styles and XML module records;
- SharedPreferences/database/serialized-state keys used only by removed code;
- assets, HTML/JavaScript/help content and remote-content loaders;
- reflection strings, class-name strings and other indirect references;
- dead branches and call sites whose only purpose was the removed subsystem.

When useful file-manager behavior shares a class with retired behavior, the useful behavior must be moved to a neutral surviving class before the old class is deleted.

## Companion-package compatibility helper

Use the absolute simplest safe implementation possible: one pure boolean helper, no object model and no state machine.

Conceptually it must do only this:

```text
hasValidCompanion():
    info = PackageManager lookup(expected external package)
    if info is missing: return false
    return signerFingerprint(info) == EXPECTED_FINGERPRINT
```

Nothing else belongs in this path.

Specifically prohibited:

- caching the result;
- storing any status object;
- version checks;
- installer-source checks;
- account checks;
- timestamps;
- countdowns;
- refresh/query operations;
- network calls;
- SKU/catalog/product logic;
- activation/evaluation/expiry state;
- callbacks/listeners;
- broadcasts;
- UI, dialogs, notifications or settings;
- persistence keys related to this check.

The helper returns one boolean and normal file-manager capability code consumes that boolean directly. If the package lookup throws/returns missing, the helper returns false. If the signing identity does not match, it returns false. No other result or state exists.

## Catalog metadata removal

The simplified companion boolean makes the old catalog/SKU layer unnecessary. Physically remove all app-owned code and resources whose only purpose is describing, querying, caching, validating, serializing or displaying catalog items.

This includes:

- SKU identifiers and catalog codes;
- catalog item/detail/state models;
- catalog query/request/result classes;
- catalog caches and refresh paths;
- catalog JSON fields and persistence keys;
- catalog-specific signatures/tokens;
- catalog UI labels, descriptions, buttons and dialogs;
- catalog-specific broadcasts, callbacks and listeners;
- branches that choose behavior based on a catalog identifier or catalog state.

No surviving file-manager path may depend on catalog metadata. The single companion-package compatibility helper is the only gate.

## Time-window/state subsystem removal

Physically remove the old time-window/status system rather than making it inert. This includes all app-owned implementation and resources for:

- evaluation periods;
- state/status persistence;
- activation state;
- expiry and remaining-time calculations;
- elapsed-time bookkeeping;
- countdown timers and callbacks;
- start/refresh/query/import/export logic;
- state enums/constants and serialized keys;
- expired/active/time-remaining dialogs, notifications and labels;
- fixed-duration evaluation logic;
- catalog-state coupling to the removed state machine.

No dormant state machine classes or persistence keys remain after rebuild.

## Developer settings cleanup

The legacy store-disable developer preference in the upstream developer settings XML must be structurally removed. Its title/summary resources, preference key, read/write code and every call site must also be removed. It must not remain as a hidden preference.

## Legal/EULA cleanup

Remove app-owned EULA/terms acceptance flows and associated runtime cruft when they are not required for normal file-manager operation:

- EULA/terms activities, dialogs and acceptance preferences;
- first-run legal gates tied only to those screens;
- app-owned legal HTML/assets and navigation entries;
- acknowledgement state used only to remember acceptance;
- obsolete vendor links and legal/promotional remote content.

Do **not** delete third-party notices or license texts whose licenses legally require redistribution or attribution. Those should be consolidated into a compact local OSS-notices asset/screen with no background work, telemetry or network dependency. No separate acceptance flow is needed for such notices unless a third-party license explicitly requires one.

## Network minimization and telemetry removal

DW File Manager should make outbound connections only when the user deliberately invokes a network-dependent file-manager feature such as a configured network share, cloud location, Web Access or another explicit user action.

Physically remove app-owned code and resources for:

- analytics and telemetry;
- crash-report uploads;
- attribution/measurement;
- background diagnostics upload;
- remote configuration;
- promotional/store content;
- automatic background pings;
- unsolicited update checks;
- data-transport pipelines used only for telemetry;
- endpoints and services used only by those paths.

Do not blindly delete networking or authentication libraries needed for normal file-manager functions. Every outbound path must be classified by call site and purpose first. User-requested SMB/FTP/SFTP/WebDAV/cloud/Web Access behavior is normal file-manager functionality and must remain working.

## Google-library audit

Do not infer purpose from package names alone. For each Google/Firebase/service-runtime/DataTransport class or manifest component, trace references before removal.

- Analytics/measurement/telemetry-only code: remove structurally.
- DataTransport used only by telemetry: remove structurally.
- Google common runtime component with no surviving caller: remove structurally.
- Google Drive/OAuth or other code required by an explicit cloud-file action: retain only the minimum required path.
- Unknown or shared utility code: prove whether it has a surviving caller before deleting it.

The untouched baseline contains no Firebase Analytics/Measurement implementation classes, so do not claim removal of code that was not present. Remove only verified Firebase/Google runtime pieces that actually exist and are unnecessary.

## Lean-build requirement

The project goal is a smaller, simpler APK with no orphaned cruft. After functional deletion, run reachability and resource audits to identify additional dead code/assets that can be removed safely.

Prioritize removal of:

- orphaned classes after subsystem deletion;
- unused layouts/drawables/strings/assets;
- dead vendor/promotional graphics;
- unused compatibility shims;
- obsolete network clients and serializers with zero surviving callers;
- duplicate or superseded resources;
- unused ABIs/native libraries only if device/feature compatibility requirements allow removal;
- stale help pages referencing removed functionality.

APK size reduction is secondary to preserving file-manager functionality and startup stability, but no known dead subsystem should remain merely because it is harmless.

## Theme requirements

Dark Glass and AMOLED Black Transparent must remain first-class themes with exact Pixel blue `#4285F4` active/selection/focus accents. The top application header must be opaque. The navigation drawer body must use the same surface/transparency as the popup menu.

## Release verification

A candidate APK is rejected unless all of the following are completed:

1. Parse DEX `class_defs`, `method_ids`, `field_ids`, `type_ids` and `string_ids`; do not rely only on printable-string scanning.
2. Generate a before/after inventory proving retired app-owned classes and members were deleted.
3. Parse the manifest and all Android resource XML; prove removed screens/preferences/components are absent.
4. Enumerate network endpoint strings and all manifest network-capable services/receivers/providers, classify each surviving path and document its user-facing purpose.
5. Prove no telemetry/analytics initialization runs at application startup.
6. Verify that no surviving app-owned class/field/method/resource/intent/provider/preference namespace uses the upstream vendor identity, except the narrowly documented external companion compatibility identifier if technically unavoidable.
7. Verify that app-owned EULA/terms acceptance activities, resources and persistence keys are absent.
8. Verify DEX checksums/signatures and string-table ordering after rebuild.
9. Verify resource-table integrity, ZIP CRCs and alignment.
10. Verify APK signing.
11. Launch-test startup and Settings.
12. Regression-test local browsing, root mode, Media, network shares, cloud locations and Web Access as applicable.
13. Verify the final APK path exists and is downloadable before presenting a user link.

No APK should be presented as complete if only a subset of these checks has been performed.