// maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
// Copyright (C) 2020 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
