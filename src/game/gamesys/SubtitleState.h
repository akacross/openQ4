// Shared SP/MP idPlayerView state; Quake 4 SDK EULA, see src/game/LICENSE.
	void DrawSubtitles();
	void ResetSubtitles();
	idUserInterface* subtitleGui = NULL;
	idStr subtitleCacheText[2];
	std::vector<OpenQ4Subtitles::Page> subtitlePages[2];
	float subtitleCacheWidth[2] = {}, subtitleCacheSize[2] = {};
	int subtitleCacheRows[2] = {};
