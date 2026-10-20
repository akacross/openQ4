# Android setup, backups and logs

The Android app is experimental. It needs your own Quake 4 1.4.2 game data;
retail files are not included in the APK. The current setup screen supports
English, German, Spanish and French. Gameplay still needs a supported controller
or keyboard; a complete standalone touch overlay is not available yet.

## Prepare the game files

1. Open **openQ4 setup**, choose a language and select **Continue**.
2. Select **Choose game folder**, then choose the `q4base` folder from your own
   Quake 4 installation. A subfolder inside Downloads or a connected USB drive
   can hold the source files.
3. Wait for copying, archive verification and preparation of bundled files.
   Required-file errors must be resolved before play. Missing optional content
   or language media produces a warning.
4. Select **Single player** or **Multiplayer** when the files are ready.

**Cancel** keeps completed archives. **Retry last operation** checks those
copies and starts the unfinished archive again. If the source folder becomes
unavailable, reconnect it or choose it again. If files were copied manually
into the app’s game-data directory, use **Check installed files**.

## Back up saved games or export logs

1. Quit the game, then reopen **openQ4 setup**. File operations become available
   after the game has finished closing.
2. Under **Backups and diagnostics**, select **Back up saved games** or
   **Export logs**. These actions do not require a successful game-data check.
3. In Android’s file picker, choose a destination and save the proposed ZIP
   filename. Choose storage outside the app if the copy must survive removal
   of the app.
4. Wait for the export-complete message. If you selected a cloud provider,
   also wait for that provider’s upload to finish.

A save backup includes the files in each game’s `savegames` folder, including
descriptions and preview images. A log export includes each game’s `logs`
folder, including setup diagnostics. The ZIP preserves those game-relative
folders and contains `openq4-export.tsv`, an inventory with file sizes and
SHA-256 checksums. Retail data, extracted packages and settings are not part of
these exports. Logs can include local file paths and server addresses; review
them before sharing.

Export reads the originals and prepares a temporary ZIP before copying it to
the selected destination. Allow free app storage for approximately the total
size of the selected files plus archive overhead, as well as space at the
destination. The app reports the exact temporary-space requirement if needed.
Each export supports up to 2 GiB of source data and 4,096 entries below the
selected folders, with bounded folder depth and portable filenames.

If export is cancelled, interrupted or fails, the original saves and logs stay
in the app. The destination can contain an empty or incomplete ZIP: remove that
failed copy in Files, then retry with a new destination. After an app restart,
retry starts a fresh export and asks for a destination again.

This screen currently exports backups; it does not import backup ZIPs. Keep
the original installation and its app data until a restore path has been
verified for your intended device and game version.

## Update without removing saves

Install updates over the existing app using the same distributor and signing
identity. Uninstalling the app or clearing its app data removes its private
saves. Make an independent backup before changing installations. Physical
device, provider and release-upgrade qualification remains in progress.
