# Stage 04 — commerce/IAB/BillingClient structural removal

Source checkpoint: Stage 03 applied to the immutable FX 9.1.0.8 baseline.

Sequential transformations:

1. `tools/stages/stage04a_sever_commerce_roots.py`
2. `tools/stages/stage04b_prune_iab_core.py`
3. `tools/stages/stage04c_remove_acquisition_proxy.py`
4. `tools/stages/stage04d_remove_web_upgrade.py`
5. `tools/stages/stage04e_remove_product_graph.py`
6. `tools/stages/stage04f_strip_shared_billing.py`
7. `tools/stages/stage04g_prune_commerce_resources.py`
8. `tools/stages/stage04h_remove_residual_commerce.py`
9. `tools/stages/stage04i_help_cleanup.py`

This stage removes the app-owned commerce/acquisition/product graph rather than hiding it.

## 04a — active commerce roots severed

- removed commerce/IAB fields from `PlusExtension`;
- removed purchase/welcome/state-update bridge methods and acquisition lifecycle work;
- replaced commerce `onCreate/onDestroy` behavior with no-op lifecycle methods while retaining useful extension registration;
- removed the commerce receiver discriminator arm from the R8-shared receiver;
- removed IAB module metadata, billing permission, and billing-service visibility queries from the manifest;
- deleted `res/xml/module_iab.xml` and its public resource declaration.

## 04b — app-owned IAB/BillingClient client core deleted

- removed isolated BillingClient callback arms/methods from R8-shared classes;
- physically deleted the complete 26-file `nextapp.fx.iab` package;
- deleted `plus/ui/a` and `plus/ui/b` commerce glue;
- deleted dedicated `k2/a,j,k,l,m,n,o,q,r,s,z` BillingClient service/client/callback classes;
- preserved R8-shared classes only where they still serve normal file-manager functionality.

## 04c — acquisition dialog / public BillingClient API removed

- deleted acquisition dialog cluster `yd/b` and `yd/c` and their isolated callback arms;
- removed the public BillingClient proxy-activity callback arms from R8-shared activity-result handlers;
- physically deleted `com/android/billingclient/api/ProxyBillingActivity`, `ProxyBillingActivityV2`, and `Purchase`;
- removed the proxy activities/version metadata from the manifest;
- removed billing registration/phenotype raw/XML assets and `billing.properties`;
- removed associated public resource declarations and stale Apktool compression entries.

## 04d — Web Access upgrade/promo module removed

- deleted `assets/web/app/Upgrade.js`;
- removed `MODULE_UPGRADE`, workspace upgrade tab, upgrade resource entry, and bundled equivalents from `WS.Base.js`;
- removed the remote `android.nextapp.com/websharing/upgrade/` loader path.

## 04e — product/SKU model graph removed

- removed R8 bridge methods whose only purpose was product/SKU streams/list operations;
- physically deleted `k2/b,c,d,g,h,i,t,u,v,x` product/query/detail classes;
- deleted generated product predicate/mapper helpers;
- verified product-ID/ProductDetails/SKU terminology is absent from surviving `k2` code.

## 04f — billing methods removed from shared R8 classes

- removed billing interface implementation and billing-only constructor/logger methods from the heavily shared `k2/y` class;
- deleted `k2/w` billing broadcast interface;
- removed BillingResult builder/bridge methods from shared classes;
- deleted `k2/f` BillingResult;
- surviving `k2` package after Stage 04 is only generic shared `e`, `p`, and `y`.

## 04g — Android commerce resources removed/neutralized

- deleted the dead upgrade banner preference class after proving it had no external callers;
- removed 30 localized commerce/acquisition resource elements across locale folders, including product code, Get/Upgrade, IAB error, purchase chooser, welcome/promo, store-disable, and old upgrade preference copy;
- removed matching `public.xml` declarations;
- preserved three live resource IDs but migrated them to neutral names/wording:
  - help section -> `doc_help_section_media_network` / `Media, Network & Sharing`;
  - device-sharing gate -> `sharing_connect_companion_required`;
  - Web Access gate -> `sharing_web_access_companion_required`.

## 04h — residual app-owned commerce methods removed

- deleted an uncalled purchase-verification method R8-merged into `mb/d`;
- deleted an uncalled billing-override metadata method R8-merged into Emoji2;
- removed an unreachable BillingClient timeout discriminator arm from the shared Fragment runnable after enumerating its constructor discriminators;
- neutralized the sharing-service unavailable-companion log message and tag.

## 04i — help cleanup

- removed the FAQ paragraph describing Google in-app billing / FX Plus purchase permission.

## Full Stage 04 verification

Final unsigned Stage 04 checkpoint APK:

- SHA-256: `5e2f8955b82821f6d2945c4e4c5b60a33367bfab991a4452b9a33a4a52fbca4f`
- size: 12,979,987 bytes
- Apktool 3.0.3 build: success
- ZIP integrity (`unzip -t`): success

Independent pinned baksmali 3.0.10 disassembly of rebuilt `classes.dex`:

- `classes.dex` SHA-256: `7913ac45b7d3847601d00ccd9919bb86a8c67d4c9920f9bd7940929fcb821e12`
- class files: **12,005**
- Stage 03 class files: 12,065
- net class-definition reduction in Stage 04: **60**

Rebuilt-Dex / package assertions:

- `nextapp.fx.iab` references: **0**
- `com.android.billingclient.api` references: **0**
- purchase request/complete/error action references: **0**
- `nextapp/fx/iab` directory: absent
- public BillingClient API directory: absent
- surviving `k2` classes: `e`, `p`, `y` only, each retained because it is R8-shared with normal non-commerce functionality
- billing/IAB/purchase manifest tokens: absent
- commerce Android resource copy: absent
- commerce FAQ copy: absent

## Important remaining boundary

The Stage 04 tree still contains **167 classes under `com.google.android.gms.internal.play_billing`** and **4 Google DataTransport classes**. They are a shaded/R8-mixed generated runtime and are not being accepted as final commerce residue.

Some of those generated classes are genuinely shared generic future/protobuf/collection/encoding helpers used by ordinary file-manager code; others are commerce/telemetry-only and must be deleted. Stage 05 will sever the concrete DataTransport/logging/scheduler/backend roots, recompute transitive reachability, physically delete unreachable generated classes, and later migrate any proven generic survivors to a neutral DW runtime namespace.

Likewise, the useful Media/Network/Web Access implementation still lives under legacy `plus`-named namespaces pending the neutral namespace/JNI migration stage.

The app-owned EULA/privacy/vendor asset flow is also deliberately still present at this checkpoint because `ExplorerActivity` still references it. It must be removed together with its startup acceptance gate in the dedicated legal/vendor stage; deleting only the asset files here would create a broken intermediate startup path.

This is an unsigned structural checkpoint, not a user-test APK or release candidate.
