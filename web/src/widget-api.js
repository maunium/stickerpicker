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
let widgetId = null

window.onmessage = event => {
	if (!window.parent || !event.data) {
		return
	}

	const request = event.data
	if (!request.requestId || !request.widgetId || !request.action || request.api !== "toWidget") {
		return
	}

	if (widgetId) {
		if (widgetId !== request.widgetId) {
			return
		}
	} else {
		widgetId = request.widgetId
	}

	let response

	if (request.action === "visibility") {
		response = {}
	} else if (request.action === "capabilities") {
		response = { capabilities: ["m.sticker"] }
	} else {
		response = { error: { message: "Action not supported" } }
	}

	window.parent.postMessage({ ...request, response }, event.origin)
}

export function sendSticker(content) {
	const data = {
		content: { ...content },
		// `name` is for Element Web (and also the spec)
		// Element Android uses content -> body as the name
		name: content.body,
	}
	// Custom field that stores the ID even for non-telegram stickers
	delete data.content.id

	// This is for Element iOS
	const widgetData = {
		...data,
		description: content.body,
		file: content.filename ?? `${content.id}.png`,
	}
	delete widgetData.content.filename
	// Element iOS explodes if there are extra fields present
	delete widgetData.content["net.maunium.telegram.sticker"]

	window.parent.postMessage({
		api: "fromWidget",
		action: "m.sticker",
		requestId: `sticker-${Date.now()}`,
		widgetId,
		data,
		widgetData,
	}, "*")
}
