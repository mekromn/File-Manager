#include <jni.h>
#include <sys/stat.h>

JNIEXPORT jint JNICALL
Java_dw_filemanager_NativeFileAccess_nativeMkfifo(JNIEnv *env, jobject thiz, jstring path) {
    (void) thiz;
    const char *native_path = (*env)->GetStringUTFChars(env, path, 0);
    if (native_path == 0) {
        return -1;
    }
    int result = mkfifo(native_path, 0666);
    (*env)->ReleaseStringUTFChars(env, path, native_path);
    return result;
}

JNIEXPORT jint JNICALL
Java_dw_filemanager_NativeFileAccess_nativeGetLastModified(JNIEnv *env, jobject thiz, jstring path) {
    (void) thiz;
    const char *native_path = (*env)->GetStringUTFChars(env, path, 0);
    if (native_path == 0) {
        return -1;
    }

    struct stat info = {0};
    int result = stat(native_path, &info);
    (*env)->ReleaseStringUTFChars(env, path, native_path);

    if (result != 0) {
        return -1;
    }
    return (jint) info.st_mtime;
}
