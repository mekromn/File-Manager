# FX Extended core rework requirements

The next accepted FX Extended build must start from the immutable FX 9.1.0.8 upstream APK (SHA-256 `19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6`). Rejected test APKs are never build inputs.

## Structural deletion, not deactivation

Legacy state/store/time-window code that is no longer part of FX Extended must be physically removed from the rebuilt DEX/resources. Making a branch unreachable, returning a constant, unregistering a screen while leaving its class, or renaming the old implementation does not count as removal.

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

There must be only one small internal helper for the external companion package. It returns a boolean after checking that the expected package is installed and that its signing identity matches the known official NextApp certificate. It must not expose or retain a richer state machine.

No version/state/SKU/catalog/time/refresh/network/account/installer-source logic belongs in this helper. No cached status object, timer, timestamp or UI page is allowed.

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

## Developer settings cleanup

The legacy store-disable developer preference in `res/k_.xml` must be structurally removed from the preference XML. Its title/summary resources, preference key, read/write code and every call site must also be removed. It must not remain as a hidden preference.

## Network minimization and telemetry removal

FX Extended should make outbound connections only when the user deliberately invokes a network-dependent file-manager feature such as a configured network share, cloud location, Web Access or another explicit user action.

Physically remove app-owned code and resources for:

- analytics and telemetry;
- crash-report uploads;
- attribution/measurement;
- background diagnostics upload;
- remote configuration;
- promotional or store content;
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

## Theme requirements

Dark Glass and AMOLED Black Transparent must remain first-class themes with exact Pixel blue `#4285F4` active/selection/focus accents. The top FX header must be opaque. The navigation drawer body must use the same surface/transparency as the popup menu.

## Release verification

A candidate APK is rejected unless all of the following are completed:

1. Parse DEX `class_defs`, `method_ids`, `field_ids`, `type_ids` and `string_ids`; do not rely only on printable-string scanning.
2. Generate a before/after inventory proving retired app-owned classes and members were deleted.
3. Parse the manifest and all Android resource XML; prove removed screens/preferences/components are absent.
4. Enumerate network endpoint strings and all manifest network-capable services/receivers/providers, classify each surviving path and document its user-facing purpose.
5. Prove no telemetry/analytics initialization runs at application startup.
6. Verify DEX checksums/signatures and string-table ordering after rebuild.
7. Verify resource-table integrity, ZIP CRCs and alignment.
8. Verify APK signing.
9. Launch-test startup and Settings.
10. Regression-test local browsing, root mode, Media, network shares, cloud locations and Web Access as applicable.

No APK should be presented as complete if only a subset of these checks has been performed.