package dw.filemanager.feed;

import android.os.Bundle;
import dw.filemanager.ui.ExplorerActivity;

/**
 * Real ExplorerActivity running intact on the feed virtual display.
 *
 * V9 intentionally does NOT override startActivity(). Android therefore gets to
 * preserve the current Activity/task/display for DW-owned child navigation instead
 * of the feed host forcing every child launch onto Display.DEFAULT_DISPLAY.
 */
public final class DwFeedActivity extends ExplorerActivity {
    @Override protected void onPostCreate(Bundle state) {
        super.onPostCreate(state);
        DwFeedRegistry.activityReady(
                this,
                getIntent().getStringExtra(DwFeedProtocol.K_SESSION));
    }
}
