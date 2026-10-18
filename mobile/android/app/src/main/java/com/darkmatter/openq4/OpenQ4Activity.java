// Standalone host for emileb's Android/GLES support in openQ4.
// SPDX-License-Identifier: GPL-3.0-or-later
package com.darkmatter.openq4;

import android.system.ErrnoException;
import android.system.Os;
import org.libsdl.app.SDLActivity;
import java.io.File;
import java.io.IOException;

/** SDL owns the Activity lifecycle; Meson owns all native compilation. */
public final class OpenQ4Activity extends SDLActivity {
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
