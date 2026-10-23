// SPDX-License-Identifier: GPL-3.0-or-later
// Production queue transitions, with counted OpenAL uploads and the real bounded
// decoder. The fixture compares every submitted PCM sample across loop seams.
#include "src/sound/SoundVorbisStream.h"
#include "src/sound/SoundSurround.h"
#include "src/sound/SoundQueue.h"
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>
#undef INT_MAX

static void Check(bool ok, const char* reason) { if (!ok) { std::fprintf(stderr, "%s\n", reason); std::exit(1); } }
template<class T> T Min(T a,T b) { return (std::min)(a,b); }
template<class T> T Max(T a,T b) { return (std::max)(a,b); }
struct idMath { static const int INT_MAX = 0x7fffffff; };
using ALuint = unsigned;
using byte = unsigned char;
using ALint = int;
using ALsizei = int;
constexpr int AL_NO_ERROR = 0;
enum { AL_INITIAL, AL_PLAYING, AL_STOPPED, AL_SOURCE_STATE, AL_BUFFERS_PROCESSED, AL_BUFFERS_QUEUED };
enum { AL_SAMPLE_OFFSET, AL_FORMAT_51CHN16 };
#define OPENQ4_OPENAL_CENTER_ROUTING_SUPPORTED 1
void alSourcei(ALuint,int,int) {}
struct idWaveFile { static const int FORMAT_PCM = 1; };
constexpr int MAX_QUEUED_BUFFERS = 3;
struct Debug { bool GetBool() const { return false; } } s_debugHardware;
struct idLib { static void Printf(const char*,...) {} };
int alIsSource(ALuint source) { return source != 0; }
static int sourceState = AL_PLAYING;
void alGetSourcei(ALuint,int property,int* value) { *value = property == AL_SOURCE_STATE ? sourceState : 0; }
void alSourceUnqueueBuffers(ALuint,int,ALuint*) {}
void alSourcePlay(ALuint) { sourceState = AL_PLAYING; }
void alDeleteBuffers(ALsizei, const ALuint*) {}
template<class T> struct List : std::vector<T> { int Num() const { return static_cast<int>(this->size()); } const T* Ptr() const { return this->data(); } };
static int alive = 0;
struct idSoundOggStream {
	SoundVorbisStream reader;
	std::vector<unsigned char> data;
	idSoundOggStream() { ++alive; }
	~idSoundOggStream() { --alive; }
	static int ReadAt(void* user, unsigned int at, void* target, int bytes) {
		auto& self = *static_cast<idSoundOggStream*>(user);
		if (at > self.data.size()) return 0;
		bytes = Min(bytes, static_cast<int>(self.data.size() - at));
		std::memcpy(target, self.data.data() + at, bytes);
		return bytes;
	}
	bool Open(const std::string& name) {
		std::ifstream file(name, std::ios::binary);
		data.assign(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
		return reader.Open(ReadAt, this, static_cast<unsigned int>(data.size()));
	}
	bool Seek(unsigned int frame) { return reader.Seek(frame); }
	int Read(short* output, int frames) { return reader.Read(output, frames); }
	int Channels() const { return reader.Channels(); }
	int Rate() const { return reader.Rate(); }
	unsigned int Frames() const { return reader.Frames(); }
};
struct idSoundSample_OpenAL {
	struct sampleBuffer_t { int numSamples = 0; const short* buffer = nullptr; int bufferSize = 0; };
	List<sampleBuffer_t> buffers;
	struct Format { struct Basic { int formatTag = 1, blockSize = 2; } basic; } format;
	ALuint openalBuffer = 0;
	int totalBufferSize = 0;
	int playLength = 0, playBegin = 0, channels = 0, rate = 0;
	bool streamed = true;
	std::string streamName;
	std::vector<short> pcm;
	bool IsStreamed() const { return streamed; }
	bool EnsureCpuPayload() { return !streamed; }
	int NumChannels() const { return channels; }
	int SampleRate() const { return rate; }
	int GetOpenALBufferFormat() const { return channels; }
	const char* GetName() const { return streamName.c_str(); }
	void Load(const char* path) {
		streamName = path;
		idSoundOggStream probe; Check(probe.Open(path), "fixture open");
		short* full = nullptr;
		playLength = stb_vorbis_decode_memory(probe.data.data(), static_cast<int>(probe.data.size()), &channels, &rate, &full);
		Check(playLength > 0, "reference PCM");
		pcm.assign(full, full + playLength * channels); std::free(full);
		totalBufferSize = playLength * channels * sizeof(short);
		format.basic.blockSize = channels * sizeof(short);
		buffers.push_back({playLength, pcm.data(), totalBufferSize});
	}
};
static std::map<ALuint,std::vector<short>> buffers;
static std::vector<short> queued;
static int uploadedMax = 0;
static bool failUpload = false;
void alBufferData(ALuint id, int, const void* data, int bytes, int) {
	uploadedMax = Max(uploadedMax, bytes);
	const short* samples = static_cast<const short*>(data);
	buffers[id].assign(samples, samples + bytes / sizeof(short));
}
void alSourceQueueBuffers(ALuint, int, const ALuint* id) { queued.insert(queued.end(), buffers[*id].begin(), buffers[*id].end()); }
int CheckALErrors() { return failUpload ? 1 : 0; }
class idSoundVoice_OpenAL {
public:
	idSoundSample_OpenAL* leadinSample = nullptr;
	idSoundSample_OpenAL* loopingSample = nullptr;
	idSoundSample_OpenAL* nextQueuedSample = nullptr;
	idSoundSample_OpenAL* oggStreamSample = nullptr;
	idSoundOggStream* oggStream = nullptr;
	int oggStreamOffset = 0, nextQueuedOffset = 0, nextQueuedBuffer = 0;
	ALuint openalSource = 1;
	ALuint openalStreamingBuffer[3] = {1,2,3};
	bool paused = true;
	bool centerRouting = false;
	bool deepRoutedQueue = false;
	float centerChannel = 0.75f;
	bool openalStreamingBufferQueued[3] = {};
	bool queuedBufferPlaybackActive = false;
	~idSoundVoice_OpenAL() { ResetQueuedBufferState(); DeleteStreamingBuffers(); }
	int StreamingBufferIndex(ALuint id) { return static_cast<int>(id) - 1; }
	int SubmitBuffer(idSoundSample_OpenAL* sample, int buffer, int offset, ALuint streamBuffer);
	void ResetQueuedBufferState();
	void AdvanceQueuedBuffer();
	bool SetNextQueuedSampleStart(idSoundSample_OpenAL* sample);
	static bool GetPlayableBufferRange(const idSoundSample_OpenAL*,int,int&,int&,int&,int&);
	bool QueueNextBuffer(ALuint buffer);
	int RoutedQueueFrames(int sampleRate);
	void DeleteStreamingBuffers();
	bool HasQueuedBufferState() const { return queuedBufferPlaybackActive || nextQueuedSample; }
	bool UsesStreamingBuffers() const { return true; }
	bool UsesBoundedQueue() const;
	bool Update();
};

// Production statics of AL_SoundVoice.cpp that the extracted bodies use.
static int soundDeepRoutedQueueVoices = 0;
static short soundRoutedQueueMono[SOUND_QUEUE_MAX_FRAMES];
static short soundRoutedQueueScratch[SOUND_QUEUE_MAX_FRAMES * 6];

// @PRODUCTION@

int main(int argc, char** argv) {
	Check(argc == 3, "provide matching mono leadin and loop fixtures");
	idSoundSample_OpenAL lead, loop;
	lead.Load(argv[1]); loop.Load(argv[2]);
	Check(lead.channels == loop.channels && lead.rate == loop.rate, "matching queue formats");
	for (int mode = 0; mode < 10; ++mode) {
		lead.streamed = mode != 1 && mode != 5 && mode != 7; lead.openalBuffer = lead.streamed ? 0 : 7;
		loop.streamed = mode != 2 && mode != 6; loop.openalBuffer = loop.streamed ? 0 : 8;
		if (mode >= 8) { lead.streamed=loop.streamed=false; lead.openalBuffer=loop.openalBuffer=0; }
		buffers[7] = lead.pcm; buffers[8] = loop.pcm;
		idSoundVoice_OpenAL voice;
		voice.centerRouting = mode >= 4 && mode != 8;
		if (mode == 7) {
			const int half = lead.playLength / 2;
			lead.buffers.clear();
			lead.buffers.push_back({half,lead.pcm.data(),half * 2});
			lead.buffers.push_back({lead.playLength,lead.pcm.data()+half,(lead.playLength-half) * 2});
		}
		voice.leadinSample = &lead;
		voice.loopingSample = mode == 3 ? &lead : &loop;
		Check(voice.SetNextQueuedSampleStart(&lead), "initial queue start");
		const int offset = mode == 3 ? lead.playLength / 3 : 0;
		voice.nextQueuedOffset = offset;
		queued.clear();
		std::vector<short> expected(lead.pcm.begin() + offset * lead.channels, lead.pcm.end());
		const auto& repeat = mode == 3 ? lead.pcm : loop.pcm;
		for (int i = 0; i < 3; ++i) expected.insert(expected.end(), repeat.begin(), repeat.end());
		if (voice.centerRouting) {
			std::vector<short> surround(expected.size() * 6);
			SoundRouteMonoToCenter(expected.data(), static_cast<int>(expected.size()), voice.centerChannel, surround.data());
			expected.swap(surround);
		}
		int calls = 0;
		while (queued.size() < expected.size()) {
			Check(voice.nextQueuedSample != nullptr && ++calls < 10000, "loop progress");
			Check(voice.QueueNextBuffer((voice.centerRouting || voice.nextQueuedSample->openalBuffer==0) ? 1 + calls % 3 : 0), "queue block");
		}
		Check(std::equal(expected.begin(), expected.end(), queued.begin()), "leadin/loop sample continuity");
		voice.ResetQueuedBufferState();
		Check(alive == 0, "stop releases all decoder state");
	}
	idSoundVoice_OpenAL voice;
	lead.streamed = true; lead.openalBuffer = 0;
	lead.buffers.clear(); lead.buffers.push_back({lead.playLength,lead.pcm.data(),lead.totalBufferSize});
	voice.leadinSample = &lead;
	voice.SetNextQueuedSampleStart(&lead);
	failUpload = true;
	Check(!voice.QueueNextBuffer(1) && alive == 0 && !voice.nextQueuedSample, "failed upload cancels decoder");
	failUpload = false;
	Check(voice.SetNextQueuedSampleStart(&lead) && voice.QueueNextBuffer(1), "recovered allocation");
	const auto oldQueueSize = queued.size();
	sourceState = AL_STOPPED; voice.paused = false;
	Check(!voice.Update() && queued.size() == oldQueueSize, "underrun requests logical-time recovery without replaying stale PCM");
	voice.ResetQueuedBufferState();
	Check(alive == 0, "underrun teardown releases decoder");
	Check(uploadedMax <= SOUND_QUEUE_DEEP_ROUTED_BUFFER_BYTES, "bounded queued PCM including centre routing");
	Check(soundDeepRoutedQueueVoices == 0, "finished voices return their deep routed slots");
	// The queue is refilled once per main-thread frame. Three buffers must ride
	// out a long frame (about one second) without exceeding the bytes per buffer
	// that the fixed and stream reservations count.
	for (int rate : {8000, 11025, 22050, 24000, 32000, 44100, 48000, 96000}) {
		for (int frameBytes : {2, 4, 12}) {
			const int frames = SoundQueueChunkFrames(rate, frameBytes);
			Check(frames >= 1 && frames * frameBytes <= SOUND_QUEUE_BUFFER_BYTES, "queue buffer within its reservation");
			Check(frames >= SOUND_QUEUE_MIN_FRAMES || frames * frameBytes == SOUND_QUEUE_BUFFER_BYTES, "queue never shallower than before");
			if (frameBytes == 2 && rate <= 48000) Check(3.0 * frames >= rate, "three mono buffers cover one second");
			if (frameBytes == 4 && rate <= 24000) Check(3.0 * frames >= rate, "three stereo buffers cover one second");
			if (frameBytes == 4 && rate <= 48000) Check(3.0 * frames >= 0.75 * rate, "three stereo buffers cover 750 ms");
			if (frameBytes == 12) Check(frames == 4096, "routed 5.1 outside the deep pool keeps one 4096-frame block");
			if (frameBytes == 12 && rate <= 48000) {
				const int deep = SoundQueueFrames(rate, 12, SOUND_QUEUE_DEEP_ROUTED_BUFFER_BYTES);
				Check(3.0 * deep >= rate && deep * 12 <= SOUND_QUEUE_DEEP_ROUTED_BUFFER_BYTES, "deep routed buffers cover one second");
			}
		}
	}
	for (int mode = 0; mode < 3; ++mode) {
		// 0: streamed Ogg, 1: CPU-resident PCM without an uploaded buffer, 2: centre-routed stream.
		idSoundVoice_OpenAL depth;
		lead.streamed = mode != 1; lead.openalBuffer = 0;
		lead.buffers.clear(); lead.buffers.push_back({lead.playLength,lead.pcm.data(),lead.totalBufferSize});
		depth.centerRouting = mode == 2;
		depth.leadinSample = &lead;
		Check(depth.SetNextQueuedSampleStart(&lead), "depth queue start");
		queued.clear(); uploadedMax = 0;
		for (ALuint buffer = 1; buffer <= 3; ++buffer) Check(depth.QueueNextBuffer(buffer), "depth queue block");
		const int outputChannels = mode == 2 ? 6 : lead.channels;
		const size_t queuedFrames = queued.size() / outputChannels;
		Check(queuedFrames >= static_cast<size_t>(Min(lead.playLength, lead.rate)), "three queued buffers hold one second");
		Check(uploadedMax <= (mode == 2 ? SOUND_QUEUE_DEEP_ROUTED_BUFFER_BYTES : SOUND_QUEUE_BUFFER_BYTES), "deeper queue keeps its per-buffer byte bound");
		Check(soundDeepRoutedQueueVoices == (mode == 2 ? 1 : 0) && depth.deepRoutedQueue == (mode == 2), "only routed voices hold a deep slot");
		std::vector<short> expected(lead.pcm.begin(), lead.pcm.begin() + Min(queuedFrames, lead.pcm.size()) * (mode == 2 ? 1 : lead.channels));
		if (mode == 2) {
			std::vector<short> surround(expected.size() * 6);
			SoundRouteMonoToCenter(expected.data(), static_cast<int>(expected.size()), depth.centerChannel, surround.data());
			expected.swap(surround);
		}
		Check(expected.size() == queued.size() && std::equal(expected.begin(), expected.end(), queued.begin()), "multi-read buffers keep sample continuity");
		depth.ResetQueuedBufferState();
		Check(alive == 0, "depth check releases decoder");
		depth.DeleteStreamingBuffers();
		Check(soundDeepRoutedQueueVoices == 0 && !depth.deepRoutedQueue, "deleting the buffers returns the deep slot");
	}
	{
		// The pool is bounded: routed voices beyond it keep 4096 frames until a slot frees.
		std::vector<idSoundVoice_OpenAL> routed(SOUND_QUEUE_DEEP_ROUTED_VOICES + 1);
		for (auto& voice : routed) voice.centerRouting = true;
		for (int i = 0; i < SOUND_QUEUE_DEEP_ROUTED_VOICES; ++i) Check(routed[i].RoutedQueueFrames(22050) == 7680, "deep routed slot");
		Check(routed.back().RoutedQueueFrames(22050) == 4096 && !routed.back().deepRoutedQueue, "pool exhausted keeps 4096 frames");
		Check(routed[0].RoutedQueueFrames(22050) == 7680 && soundDeepRoutedQueueVoices == SOUND_QUEUE_DEEP_ROUTED_VOICES, "slot reuse is not double counted");
		routed[0].DeleteStreamingBuffers();
		Check(routed.back().RoutedQueueFrames(22050) == 7680 && routed.back().deepRoutedQueue, "freed slot is reused");
	}
	Check(soundDeepRoutedQueueVoices == 0, "destroyed voices return every deep slot");
	std::puts("PASS production queue: leadin/loop, mixed static/streamed, offset, three scratch buffers, one-second depth, cancellation and release");
}
