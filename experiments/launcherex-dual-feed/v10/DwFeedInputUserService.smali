.class public final Ldw/filemanager/feed/DwFeedInputUserService;
.super Landroid/os/Binder;
.source "DwFeedInputUserService.java"

# This class is instantiated by Shizuku as uid 2000. UserService processes are
# exempt from normal app hidden-API restrictions, so the system InputManager can
# be used directly and Android's real input dispatcher chooses the topmost window
# on the feed display (PopupWindow/Dialog/viewer/root Activity).

.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Landroid/os/Binder;-><init>()V
    return-void
.end method

.method protected onTransact(ILandroid/os/Parcel;Landroid/os/Parcel;I)Z
    .registers 9

    const/4 v0, 0x1
    if-ne p1, v0, :super_call

    :try_start_3
    invoke-virtual {p2}, Landroid/os/Parcel;->readInt()I
    move-result v1

    sget-object v2, Landroid/view/MotionEvent;->CREATOR:Landroid/os/Parcelable$Creator;
    invoke-interface {v2, p2}, Landroid/os/Parcelable$Creator;->createFromParcel(Landroid/os/Parcel;)Ljava/lang/Object;
    move-result-object v2
    check-cast v2, Landroid/view/MotionEvent;

    invoke-virtual {v2, v1}, Landroid/view/InputEvent;->setDisplayId(I)V

    invoke-static {}, Landroid/hardware/input/InputManagerGlobal;->getInstance()Landroid/hardware/input/InputManagerGlobal;
    move-result-object v1
    if-eqz v1, :recycle_ok

    const/4 v3, 0x0
    invoke-virtual {v1, v2, v3}, Landroid/hardware/input/InputManagerGlobal;->injectInputEvent(Landroid/view/InputEvent;I)Z

    :recycle_ok
    invoke-virtual {v2}, Landroid/view/MotionEvent;->recycle()V
    :try_end_1d
    .catchall {:try_start_3 .. :try_end_1d} :catchall_20

    const/4 v0, 0x1
    return v0

    :catchall_20
    move-exception v1
    # Oneway input must never crash the privileged service because a single bad
    # sample would otherwise break the entire touch stream. Drop only that sample.
    const/4 v0, 0x1
    return v0

    :super_call
    invoke-super {p0, p1, p2, p3, p4}, Landroid/os/Binder;->onTransact(ILandroid/os/Parcel;Landroid/os/Parcel;I)Z
    move-result v0
    return v0
.end method
