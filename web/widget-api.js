// Copyright (c) 2020 Tulir Asokan
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
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

	window.parent.postMessage({
		...request,
		response: request.action === "capabilities" ? {
			capabilities: ["m.sticker"],
		} : {
			error: { message: "Action not supported" },
		},
	}, event.origin)
}

export function sendSticker(content) {
	const data = {
		content,
		// `name` is for Element Web (and also the spec)
		// Element Android uses content -> body as the name
		name: content.body,
	}

	// This is for Element iOS
	const widgetData = {
		...data,
		description: content.body,
		file: `${content["net.maunium.telegram.sticker"].id}.png`,
	}
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
