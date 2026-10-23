// Copyright (C) 2026 openQ4 contributors. SPDX-License-Identifier: GPL-3.0-or-later
#ifndef OPENQ4_VOICE_CHAT_H
#define OPENQ4_VOICE_CHAT_H
void SoundVoiceChat_InitCommands();
void SoundVoiceChat_Render();
// Must run before destroying the OpenAL context, including hotplug/restart.
void SoundVoiceChat_Shutdown();
#endif
