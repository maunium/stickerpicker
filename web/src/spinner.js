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
import { html } from "../lib/htm/preact.js"

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
