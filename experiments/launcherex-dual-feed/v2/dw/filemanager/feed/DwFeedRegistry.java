package dw.filemanager.feed;

import android.app.ActivityOptions;
import android.content.Context;
import android.content.Intent;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import java.util.HashMap;
import java.util.Map;
import dw.filemanager.ui.ExplorerActivity;

/** Owns real ExplorerActivity sessions whose virtual-display output is the LauncherEx SurfaceView. */
final class DwFeedRegistry {
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static final Map<String,Session> SESSIONS=new HashMap<>();
    private static Context app;
    static final class Session {
        String id,page;int width,height,density;Messenger reply;Surface output;VirtualDisplay display;ExplorerActivity activity;boolean ready;
    }
    static void init(Context c){app=c.getApplicationContext();}
    static void create(String id,String page,int width,int height,int density,Surface output,Messenger reply){
        if(app==null)return;close(id);
        if(id==null||output==null||!output.isValid()||width<=0||height<=0||!(DwFeedProtocol.PAGE_HOME.equals(page)||DwFeedProtocol.PAGE_RECENT.equals(page))){sendError(reply,id,"bad_request");return;}
        Session s=new Session();s.id=id;s.page=page;s.width=width;s.height=height;s.density=Math.max(120,density);s.reply=reply;s.output=output;
        try{
            DisplayManager dm=(DisplayManager)app.getSystemService(Context.DISPLAY_SERVICE);if(dm==null)throw new IllegalStateException("no_display_manager");
            int flags=DisplayManager.VIRTUAL_DISPLAY_FLAG_OWN_CONTENT_ONLY|DisplayManager.VIRTUAL_DISPLAY_FLAG_PRESENTATION;
            s.display=dm.createVirtualDisplay("DW Feed "+page,width,height,s.density,output,flags);
            if(s.display==null||s.display.getDisplay()==null)throw new IllegalStateException("virtual_display_failed");
            SESSIONS.put(id,s);
            Intent intent=new Intent(app,DwFeedActivity.class).putExtra(DwFeedProtocol.K_SESSION,id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_MULTIPLE_TASK|Intent.FLAG_ACTIVITY_NO_ANIMATION);
            ActivityOptions opts=ActivityOptions.makeBasic().setLaunchDisplayId(s.display.getDisplay().getDisplayId());
            app.startActivity(intent,opts.toBundle());
            MAIN.postDelayed(()->{Session q=SESSIONS.get(id);if(q!=null&&!q.ready)fail(q,"activity_timeout");},5000);
        }catch(Throwable t){fail(s,"create_failed:"+t.getClass().getSimpleName());}
    }
    static void activityReady(ExplorerActivity activity,String id){
        Session s=SESSIONS.get(id);if(s==null){activity.finish();return;}s.activity=activity;
        try{
            View decor=activity.getWindow().getDecorView();
            decor.post(()->{
                Session q=SESSIONS.get(id);if(q!=s||q.activity==null)return;
                try{
                    q.activity.A(q.page);
                    decor.postDelayed(()->markReady(q),120);
                }catch(Throwable t){fail(q,"navigate_failed:"+t.getClass().getSimpleName());}
            });
        }catch(Throwable t){fail(s,"activity_ready_failed:"+t.getClass().getSimpleName());}
    }
    private static void markReady(Session s){
        if(s==null||SESSIONS.get(s.id)!=s||s.ready)return;
        try{Bundle b=new Bundle();b.putString(DwFeedProtocol.K_SESSION,s.id);Message m=Message.obtain(null,DwFeedProtocol.MSG_READY);m.setData(b);s.reply.send(m);s.ready=true;}
        catch(Throwable t){fail(s,"ready_failed:"+t.getClass().getSimpleName());}
    }
    static void input(String id,MotionEvent event){
        Session s=SESSIONS.get(id);if(s==null||s.activity==null||event==null){if(event!=null)event.recycle();return;}
        MotionEvent copy=MotionEvent.obtain(event);event.recycle();
        MAIN.post(()->{try{if(SESSIONS.get(id)==s&&s.activity!=null)s.activity.dispatchTouchEvent(copy);}finally{copy.recycle();}});
    }
    static void close(String id){Session s=SESSIONS.remove(id);if(s==null)return;cleanup(s);}
    private static void cleanup(Session s){
        try{if(s.activity!=null)s.activity.finish();}catch(Throwable ignored){}
        try{if(s.display!=null)s.display.release();}catch(Throwable ignored){}
        try{if(s.output!=null)s.output.release();}catch(Throwable ignored){}
    }
    private static void fail(Session s,String why){if(s==null)return;sendError(s.reply,s.id,why);if(s.id!=null&&SESSIONS.get(s.id)==s)SESSIONS.remove(s.id);cleanup(s);}
    private static void sendError(Messenger reply,String id,String why){if(reply==null)return;try{Bundle b=new Bundle();b.putString(DwFeedProtocol.K_SESSION,id);b.putString(DwFeedProtocol.K_ERROR,why);Message m=Message.obtain(null,DwFeedProtocol.MSG_ERROR);m.setData(b);reply.send(m);}catch(Throwable ignored){}}
    private DwFeedRegistry(){}
}
