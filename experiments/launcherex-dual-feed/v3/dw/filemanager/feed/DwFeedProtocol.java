package dw.filemanager.feed;
public final class DwFeedProtocol {
    public static final int MSG_CREATE=1,MSG_READY=2,MSG_ERROR=3,MSG_CLOSE=4,MSG_INPUT=5;
    public static final String K_SESSION="session",K_PAGE="page",K_WIDTH="width",K_HEIGHT="height",K_DENSITY="density",K_SURFACE="surface",K_EVENT="event",K_ERROR="error";
    public static final String PAGE_HOME="home",PAGE_RECENT="recently_updated";
    public static final String LAUNCHER_PACKAGE="dev.launcherex";
    private DwFeedProtocol(){}
}
