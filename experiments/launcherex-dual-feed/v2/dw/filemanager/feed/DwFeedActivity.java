package dw.filemanager.feed;

import android.os.Bundle;
import dw.filemanager.ui.ExplorerActivity;

/** Real ExplorerActivity running intact on the feed virtual display. */
public final class DwFeedActivity extends ExplorerActivity {
    @Override protected void onPostCreate(Bundle state){
        super.onPostCreate(state);
        DwFeedRegistry.activityReady(this,getIntent().getStringExtra(DwFeedProtocol.K_SESSION));
    }
    @Override public void startActivity(android.content.Intent intent){
        android.app.ActivityOptions o=android.app.ActivityOptions.makeBasic().setLaunchDisplayId(android.view.Display.DEFAULT_DISPLAY);
        super.startActivity(intent,o.toBundle());
    }
    @Override public void startActivity(android.content.Intent intent,Bundle options){
        android.app.ActivityOptions o=android.app.ActivityOptions.makeBasic().setLaunchDisplayId(android.view.Display.DEFAULT_DISPLAY);
        super.startActivity(intent,o.toBundle());
    }
}
