package dw.filemanager.feed;

import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.view.MotionEvent;
import android.view.Surface;

/** Explicit caller-validated feed host endpoint for LauncherEx. */
public final class DwFeedService extends Service {
    private Messenger incoming;
    @Override public void onCreate(){super.onCreate();DwFeedRegistry.init(this);incoming=new Messenger(new Handler(Looper.getMainLooper(),this::handle));}
    @Override public IBinder onBind(Intent intent){return incoming.getBinder();}
    private boolean handle(Message msg){
        if(!isLauncherUid(msg.sendingUid))return true;Bundle b=msg.getData();if(b==null)return true;
        if(msg.what==DwFeedProtocol.MSG_CREATE){
            Surface surface=(Surface)b.getParcelable(DwFeedProtocol.K_SURFACE);
            DwFeedRegistry.create(b.getString(DwFeedProtocol.K_SESSION),b.getString(DwFeedProtocol.K_PAGE),b.getInt(DwFeedProtocol.K_WIDTH),b.getInt(DwFeedProtocol.K_HEIGHT),b.getInt(DwFeedProtocol.K_DENSITY),surface,msg.replyTo);
        }else if(msg.what==DwFeedProtocol.MSG_CLOSE){DwFeedRegistry.close(b.getString(DwFeedProtocol.K_SESSION));}
        else if(msg.what==DwFeedProtocol.MSG_INPUT){MotionEvent e=(MotionEvent)b.getParcelable(DwFeedProtocol.K_EVENT);DwFeedRegistry.input(b.getString(DwFeedProtocol.K_SESSION),e);}
        return true;
    }
    private boolean isLauncherUid(int uid){if(uid<=0)return false;PackageManager pm=getPackageManager();String[] pkgs=pm.getPackagesForUid(uid);if(pkgs==null)return false;for(String p:pkgs)if(DwFeedProtocol.LAUNCHER_PACKAGE.equals(p))return true;return false;}
}
