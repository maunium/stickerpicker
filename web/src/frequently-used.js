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

const FREQUENTLY_USED_STORAGE_KEY = 'mauFrequentlyUsedStickerIDs'
const FREQUENTLY_USED_STORAGE_CACHE_KEY = 'mauFrequentlyUsedStickerCache'

let FREQUENTLY_USED = JSON.parse(window.localStorage[FREQUENTLY_USED_STORAGE_KEY] ?? '{}')
let FREQUENTLY_USED_SORTED = null

const sortFrequentlyUsedEntries = (entry1, entry2) => {
	const [, [count1, date1]] = entry1
	const [, [count2, date2]] = entry2
	return count2 === count1 ? date2 - date1 : count2 - count1
}

export const setFrequentlyUsedStorage = (frequentlyUsed) => {
	FREQUENTLY_USED = frequentlyUsed ?? {}
	window.localStorage[FREQUENTLY_USED_STORAGE_KEY] = JSON.stringify(FREQUENTLY_USED)
	FREQUENTLY_USED_SORTED = null
}

export const setFrequentlyUsedCacheStorage = (stickers) => {
	const toPutInCache = stickers.map(sticker => [sticker.id, sticker])
	window.localStorage[FREQUENTLY_USED_STORAGE_CACHE_KEY] = JSON.stringify(toPutInCache)
}

export const add = (id) => {
	let FREQUENTLY_USED_COPY = { ...FREQUENTLY_USED }
	const [count] = FREQUENTLY_USED_COPY[id] || [0]
	FREQUENTLY_USED_COPY[id] = [count + 1, Date.now()]
	setFrequentlyUsedStorage(FREQUENTLY_USED_COPY)
}

export const get = (limit = 16) => {
	if (FREQUENTLY_USED_SORTED === null) {
		FREQUENTLY_USED_SORTED = Object.entries(FREQUENTLY_USED || {})
			.sort(sortFrequentlyUsedEntries)
			.map(([emoji]) => emoji)
	}
	return FREQUENTLY_USED_SORTED.slice(0, limit)
}

export const getFromCache = () => {
	return Object.values(JSON.parse(localStorage[FREQUENTLY_USED_STORAGE_CACHE_KEY] ?? '[]'))
}

export const remove = (id) => {
	let FREQUENTLY_USED_COPY = { ...FREQUENTLY_USED }
	if (FREQUENTLY_USED_COPY[id]) {
		delete FREQUENTLY_USED_COPY[id]
		setFrequentlyUsedStorage(FREQUENTLY_USED_COPY)
	}
}

export const removeMultiple = (ids) => {
	let FREQUENTLY_USED_COPY = { ...FREQUENTLY_USED }
	ids.forEach((id) => {
		delete FREQUENTLY_USED_COPY[id]
	})
	setFrequentlyUsedStorage(FREQUENTLY_USED_COPY)
}

export const removeAll = setFrequentlyUsedStorage

const compareStorageWith = (packs) => {
	const stickersIDsFromPacks = packs.map((pack) => pack.stickers).flat().map((sticker) => sticker.id)
	const stickersIDsFromFrequentlyUsedStorage = get()

	const notFound = stickersIDsFromFrequentlyUsedStorage.filter((id) => !stickersIDsFromPacks.includes(id))
	const found = stickersIDsFromFrequentlyUsedStorage.filter((id) => !notFound.includes(id))

	return { found, notFound }
}

export const removeNotFoundFromStorage = (packs) => {
	const { found, notFound } = compareStorageWith(packs)
	removeMultiple(notFound)
	return found
}
