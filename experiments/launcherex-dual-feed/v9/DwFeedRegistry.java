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
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import dw.filemanager.shizuku.ShizukuBridge;
import dw.filemanager.ui.ExplorerActivity;

/** Readable source corresponding to the V9 feed-host DEX. */
final class DwFeedRegistry {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final Map<String, Session> SESSIONS = new HashMap<>();
    private static Context app;

    static final class Session {
        String id, page;
        int width, height, density;
        Messenger reply;
        Surface output;
        VirtualDisplay display;
        ExplorerActivity activity;
        boolean ready;
        volatile String launchDiag;
        volatile Process launchProcess;
    }

    static void init(Context c) {
        app = c.getApplicationContext();
    }

    static void create(String id, String page, int width, int height, int density,
                       Surface output, Messenger reply) {
        if (app == null) return;
        close(id);
        if (id == null || output == null || !output.isValid() || width <= 0 || height <= 0 ||
                !(DwFeedProtocol.PAGE_HOME.equals(page) ||
                  DwFeedProtocol.PAGE_RECENT.equals(page))) {
            sendError(reply, id, "bad_request");
            return;
        }

        Session s = new Session();
        s.id = id;
        s.page = page;
        s.width = width;
        s.height = height;
        s.density = Math.max(120, density);
        s.reply = reply;
        s.output = output;

        DisplayManager dm = (DisplayManager) app.getSystemService(Context.DISPLAY_SERVICE);
        if (dm == null) {
            fail(s, "display_create_failed:IllegalStateException:no_display_manager");
            return;
        }
        try {
            s.display = dm.createVirtualDisplay(
                    "DW Feed " + page, width, height, s.density, output, 0);
            if (s.display == null || s.display.getDisplay() == null) {
                throw new IllegalStateException("virtual_display_failed");
            }
        } catch (Throwable t) {
            fail(s, "display_create_failed:" + describe(t));
            return;
        }

        SESSIONS.put(id, s);
        try {
            Intent intent = new Intent(app, DwFeedActivity.class)
                    .putExtra(DwFeedProtocol.K_SESSION, id)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK |
                              Intent.FLAG_ACTIVITY_MULTIPLE_TASK |
                              Intent.FLAG_ACTIVITY_NO_ANIMATION);
            ActivityOptions opts = ActivityOptions.makeBasic()
                    .setLaunchDisplayId(s.display.getDisplay().getDisplayId());
            app.startActivity(intent, opts.toBundle());
        } catch (Throwable t) {
            if (t instanceof SecurityException) {
                String shellError = launchViaShizuku(s);
                if (shellError != null) {
                    fail(s, "activity_launch_failed:" + describe(t) + ";" + shellError);
                    return;
                }
            } else {
                fail(s, "activity_launch_failed:" + describe(t));
                return;
            }
        }

        MAIN.postDelayed(() -> {
            Session q = SESSIONS.get(id);
            if (q == null || q.ready) return;
            String trace = q.launchDiag;
            fail(q, trace == null ? "activity_timeout:no_shizuku_trace"
                                  : "activity_timeout:" + trace);
        }, 5000);
    }

    private static String launchViaShizuku(Session s) {
        if (!ShizukuBridge.isAuthorized()) return "shizuku_unavailable";
        try {
            if (s.display == null || s.display.getDisplay() == null) return "display_gone";
            int displayId = s.display.getDisplay().getDisplayId();
            String cmd = "/system/bin/am start -W --user current --display " + displayId +
                    " -f 0x18010000" +
                    " -n com.mekromn.dwfilemanager/dw.filemanager.feed.DwFeedActivity" +
                    " --es session " + s.id + " 2>&1";
            Process p = ShizukuBridge.startCommand(cmd);
            if (p == null) return "shizuku_process_null";
            s.launchProcess = p;
            s.launchDiag = "shizuku_started";
            Thread worker = new Thread(() -> traceShizukuLaunch(s, p),
                    "DWFeed-shizuku-launch-trace");
            worker.setDaemon(true);
            worker.start();
            return null;
        } catch (Throwable t) {
            return "shizuku_exception:" + describe(t);
        }
    }

    private static void traceShizukuLaunch(Session s, Process p) {
        try {
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder out = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) {
                if (out.length() >= 300) continue;
                if (out.length() != 0) out.append(" | ");
                out.append(line);
            }
            r.close();
            int rc = p.waitFor();
            StringBuilder diag = new StringBuilder("shizuku_rc_").append(rc);
            if (out.length() != 0) diag.append(':').append(out);
            s.launchDiag = diag.toString();
        } catch (Throwable t) {
            s.launchDiag = "shizuku_trace_exception:" + describe(t);
        } finally {
            s.launchProcess = null;
        }
    }

    static void activityReady(ExplorerActivity activity, String id) {
        Session s = SESSIONS.get(id);
        if (s == null) {
            activity.finish();
            return;
        }
        s.activity = activity;
        try {
            View decor = activity.getWindow().getDecorView();
            decor.post(() -> {
                Session q = SESSIONS.get(id);
                if (q != s || q.activity == null) return;
                try {
                    if (DwFeedProtocol.PAGE_RECENT.equals(q.page)) {
                        // Exact catalog route used by DW's own RecentHomeItem.
                        q.activity.A(jb.d.k.f);
                    }
                    // PAGE_HOME intentionally stays on the fresh ExplorerActivity's
                    // native Home surface. A("home") is not a Home-route API.
                    decor.postDelayed(() -> markReady(q), 120);
                } catch (Throwable t) {
                    fail(q, "navigate_failed:" + describe(t));
                }
            });
        } catch (Throwable t) {
            fail(s, "activity_ready_failed:" + describe(t));
        }
    }

    private static void markReady(Session s) {
        if (s == null || SESSIONS.get(s.id) != s || s.ready) return;
        try {
            Bundle b = new Bundle();
            b.putString(DwFeedProtocol.K_SESSION, s.id);
            Message m = Message.obtain(null, DwFeedProtocol.MSG_READY);
            m.setData(b);
            s.reply.send(m);
            s.ready = true;
        } catch (Throwable t) {
            fail(s, "ready_failed:" + describe(t));
        }
    }

    /**
     * DwFeedService's Messenger handler is already bound to the main looper.
     * Dispatch directly to the real Activity instead of cloning the event and
     * scheduling another main-loop Runnable for every MOVE sample.
     */
    static void input(String id, MotionEvent event) {
        if (event == null) return;
        Session s = SESSIONS.get(id);
        try {
            if (s != null && s.activity != null) {
                s.activity.dispatchTouchEvent(event);
            }
        } finally {
            event.recycle();
        }
    }

    static void close(String id) {
        Session s = SESSIONS.remove(id);
        if (s != null) cleanup(s);
    }

    private static void cleanup(Session s) {
        try { if (s.launchProcess != null) s.launchProcess.destroy(); }
        catch (Throwable ignored) {}
        try { if (s.activity != null) s.activity.finish(); }
        catch (Throwable ignored) {}
        try { if (s.display != null) s.display.release(); }
        catch (Throwable ignored) {}
        try { if (s.output != null) s.output.release(); }
        catch (Throwable ignored) {}
    }

    private static void fail(Session s, String why) {
        if (s == null) return;
        sendError(s.reply, s.id, why);
        if (s.id != null && SESSIONS.get(s.id) == s) SESSIONS.remove(s.id);
        cleanup(s);
    }

    private static String describe(Throwable t) {
        if (t == null) return "Unknown";
        String type = t.getClass().getSimpleName();
        String msg = t.getMessage();
        if (msg == null || msg.length() == 0) return type;
        msg = msg.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ');
        while (msg.contains("  ")) msg = msg.replace("  ", " ");
        if (msg.length() > 180) msg = msg.substring(0, 180);
        return type + ':' + msg;
    }

    private static void sendError(Messenger reply, String id, String why) {
        if (reply == null) return;
        try {
            Bundle b = new Bundle();
            b.putString(DwFeedProtocol.K_SESSION, id);
            b.putString(DwFeedProtocol.K_ERROR, why);
            Message m = Message.obtain(null, DwFeedProtocol.MSG_ERROR);
            m.setData(b);
            reply.send(m);
        } catch (Throwable ignored) {}
    }

    private DwFeedRegistry() {}
}
