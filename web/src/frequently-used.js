// Copyright (c) 2020 Tulir Asokan
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
const FREQUENTLY_USED = JSON.parse(window.localStorage.mauFrequentlyUsedStickerIDs || "{}")
let FREQUENTLY_USED_SORTED = null

export const add = id => {
	const [count] = FREQUENTLY_USED[id] || [0]
	FREQUENTLY_USED[id] = [count + 1, Date.now()]
	window.localStorage.mauFrequentlyUsedStickerIDs = JSON.stringify(FREQUENTLY_USED)
	FREQUENTLY_USED_SORTED = null
}

export const get = (limit = 16) => {
	if (FREQUENTLY_USED_SORTED === null) {
		FREQUENTLY_USED_SORTED = Object.entries(FREQUENTLY_USED)
			.sort(([, [count1, date1]], [, [count2, date2]]) =>
				count2 === count1 ? date2 - date1 : count2 - count1)
			.map(([emoji]) => emoji)
	}
	return FREQUENTLY_USED_SORTED.slice(0, limit)
}
