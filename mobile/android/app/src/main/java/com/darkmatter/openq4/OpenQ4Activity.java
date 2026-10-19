// Standalone host for emileb's Android/GLES support in openQ4.
// SPDX-License-Identifier: GPL-3.0-or-later
package com.darkmatter.openq4;

import android.annotation.TargetApi;
import android.graphics.Color;
import android.graphics.Insets;
import android.os.Build;
import android.os.Bundle;
import android.system.ErrnoException;
import android.system.Os;
import android.view.KeyEvent;
import android.view.ViewGroup;
import android.view.WindowInsets;
import org.libsdl.app.SDLActivity;
import java.io.File;
import java.io.IOException;

/** SDL owns the Activity lifecycle; Meson owns all native compilation. */
public final class OpenQ4Activity extends SDLActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (!mBrokenLibraries && mLayout != null && Build.VERSION.SDK_INT >= 30) {
            keepOutOfDisplayCutout(mLayout);
        }
    }

    @TargetApi(30)
    private static void keepOutOfDisplayCutout(ViewGroup layout) {
        // SDL allows the surface under display cutouts on Android 11+. The
        // stock HUD and in-world GUIs still use the complete render target.
        // Keep that target inside the cutout, preserving one coordinate space
        // for rendering, retained UI and SDL input instead of clipping controls.
        layout.setBackgroundColor(Color.BLACK);
        layout.setOnApplyWindowInsetsListener((view, insets) -> {
            Insets cutout = insets.getInsets(WindowInsets.Type.displayCutout());
            view.setPadding(cutout.left, cutout.top, cutout.right, cutout.bottom);
            // Children, including SDL's surface and text input, receive the
            // remaining system/IME insets relative to this padded content.
            return insets.inset(cutout);
        });
        layout.requestApplyInsets();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (isFinishing()) return;
        if (mBrokenLibraries || !mActivityCreated) {
            // There is no native UI to navigate after a failed SDL load.
            // SDL's default handler calls JNI, so do not enter it here.
            finish();
            return;
        }
        // Gesture navigation reaches this callback without a hardware key.
        // Use the same SDL Back event as a physical button: the engine routes
        // it through its current menu, gameplay pause or fatal-error console.
        SDLActivity.onNativeKeyDown(KeyEvent.KEYCODE_BACK);
        SDLActivity.onNativeKeyUp(KeyEvent.KEYCODE_BACK);
    }

    @Override
    protected String[] getLibraries() {
        return new String[] { "SDL3", "quake4" };
    }

    @Override
    protected String[] getArguments() {
        // SDL invokes this on SDLThread, so first-run asset extraction does not
        // block the Android UI thread or alter input owned by the Activity.
        try {
            File retailRoot = getExternalFilesDir(null);
            if (retailRoot == null) {
                throw new IOException("App-specific external storage is unavailable");
            }
            requireDirectory(new File(retailRoot, "q4base"));
            File saveRoot = new File(getFilesDir(), "saves");
            requireDirectory(saveRoot);
            // Early native fatal diagnostics run before fs_savepath is parsed.
            Os.setenv("OPENQ4_SAVE_ROOT", saveRoot.getAbsolutePath(), true);
            File contentRoot = extractPackage();
            Os.setenv("OPENQ4_NATIVE_LIBS", getApplicationInfo().nativeLibraryDir, true);
            Os.setenv("OPENQ4_CONTENT_ROOT", contentRoot.getAbsolutePath(), true);
            boolean multiplayer = getIntent().getBooleanExtra("multiplayer", false);
            return new String[] {
                "+set", "fs_basepath", retailRoot.getAbsolutePath(),
                "+set", "fs_savepath", saveRoot.getAbsolutePath(),
                "+set", "fs_cachepath", getCacheDir().getAbsolutePath(),
                "+set", "fs_game", "baseoq4",
                "+set", "si_gameType", multiplayer ? "DM" : "singleplayer",
                "+set", "ui_autoJoin", "0",
                "+set", "r_renderApi", "gles",
                "+set", "r_renderer", "glesd3",
                "+set", "r_fullscreen", "0",
                "+set", "in_tty", "0",
                "+set", "logFile", "2",
                "+set", "logFileName", "logs/openq4.log"
            };
        } catch (IOException | ErrnoException error) {
            // SDL/logcat retains the actionable cause; never run with partial
            // package data or fall back to an unintended writable directory.
            throw new IllegalStateException("Could not prepare openQ4 storage", error);
        }
    }

    private static void requireDirectory(File directory) throws IOException {
        if (!directory.isDirectory() && !directory.mkdirs()) {
            throw new IOException("Cannot create directory: " + directory);
        }
    }

    private File extractPackage() throws IOException, ErrnoException {
        return PackageStorage.extract(getAssets(), getFilesDir());
    }
}
