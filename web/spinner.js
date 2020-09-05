// Copyright (c) 2020 Tulir Asokan
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
import { html } from "https://unpkg.com/htm/preact/index.mjs?module"

export const Spinner = ({ size = 40, noCenter = false, noMargin = false, green = false }) => {
	let margin = 0
	if (!isNaN(+size)) {
		size = +size
		margin = noMargin ? 0 : `${Math.round(size / 6)}px`
		size = `${size}px`
	}
	const noInnerMargin = !noCenter || !margin
	const comp = html`
        <div style="width: ${size}; height: ${size}; margin: ${noInnerMargin ? 0 : margin} 0;"
             class="sk-chase ${green && "green"}">
            <div class="sk-chase-dot" />
            <div class="sk-chase-dot" />
            <div class="sk-chase-dot" />
            <div class="sk-chase-dot" />
            <div class="sk-chase-dot" />
            <div class="sk-chase-dot" />
        </div>
    `
	if (!noCenter) {
		return html`<div style="margin: ${margin} 0;" class="sk-center-wrapper">${comp}</div>`
	}
	return comp
}
