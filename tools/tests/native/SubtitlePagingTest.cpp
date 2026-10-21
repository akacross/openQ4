// Copyright (C) 2026 openQ4 contributors.
#include "src/game/gamesys/SubtitlePaging.h"
#include <cassert>
#include <cstdio>
#include <limits>
using namespace OpenQ4Subtitles;
static int Glyph(const char* p, int n, float& width) {
	width = 1;
	return static_cast<unsigned char>(*p) >= 0xc0 && n > 1 ? 2 : 1;
}
int main() {
	assert(CanvasBottom(16.0f/9, false) == 570 && CanvasBottom(16.0f/9, true) == 640);
	for (float aspect : {4.0f/3, 9.0f/16}) {
		const float bottom = CanvasBottom(aspect, true);
		assert(bottom < 360 + 202.5f * aspect && bottom > 360);
		assert(bottom - (12 + 2 * 34 * 1.4f * 2) > 360 - 202.5f * aspect);
	}
	auto pages = Paginate("one two three four five six", 7, 2, Glyph);
	assert(pages.size() == 3 && pages[0].lines[0] == "one two" && pages[0].lines[1] == "three");
	assert(pages[1].lines[0] == "four" && pages[1].lines[1] == "five");
	assert(PageAt(pages, -5, 1000) == 0 && PageAt(pages, 1000, 1000) == 2);
	int last = 0;
	for (int time = 0; time < 1000; ++time) { int at = PageAt(pages,time,1000); assert(at >= last); last=at; }
	assert(Paginate(" \n\t\r ", 8, 2, Glyph).empty());
	assert(Paginate("text", 0, 1, Glyph).empty());
	assert(Paginate("text", std::numeric_limits<float>::quiet_NaN(), 1, Glyph).empty());
	assert(PageAt({}, 5, 100) == -1 && PageAt(pages, 5, 0) == -1);
	pages = Paginate("abc\ndef\r\nghi", 20, 2, Glyph);
	assert(pages.size() == 2 && pages[0].lines[1] == "def" && pages[1].lines[0] == "ghi");
	pages = Paginate("abcdefghijk", 3, 1, Glyph);
	assert(pages.size() == 4 && pages[0].lines[0] == "abc" && pages[3].lines[0] == "jk");
	pages = Paginate("\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9\xc3\xa9", 2, 1, Glyph);
	assert(pages.size() == 3 && pages[0].lines[0].size() == 4 && pages[2].lines[0].size() == 2);
	pages = Paginate("abc", .1f, 2, Glyph); // Even an oversized glyph makes progress.
	assert(pages.size() == 2 && pages[0].lines[0] == "a" && pages[0].lines[1] == "b");
	pages = Paginate(std::string(10000, 'x').c_str(), 80, 2, Glyph);
	assert(pages.back().end == 4096 && pages.size() < 256);
	pages = Paginate("abcdef", 2, 1, [](const char*,int,float& w) { w=1;return 0; });
	assert(pages.size() == 3); // Malformed input cannot stall pagination.
	std::puts("Subtitle pagination: wrapping, timing, overlap rows, UTF-8 and bounds passed");
}
