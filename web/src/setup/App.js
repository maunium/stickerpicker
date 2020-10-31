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
import { useEffect, useState } from "../../lib/preact/hooks.js"
import { html } from "../../lib/htm/preact.js"

import LoginView from "./LoginView.js"
import Spinner from "../Spinner.js"
import * as matrix from "./matrix-api.js"
import * as sticker from "./sticker-api.js"

const App = () => {
	const [loggedIn, setLoggedIn] = useState(Boolean(localStorage.mxAccessToken))
	const [widgetSecret, setWidgetSecret] = useState(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState(null)

	if (!loggedIn) {
		return html`
			<${LoginView}
				onLoggedIn=${() => setLoggedIn(Boolean(localStorage.mxAccessToken))}
			/>`
	}

	useEffect(() => {
		if (widgetSecret === null) {
			setLoading(true)
			const whoamiReceived = data => {
				setLoading(false)
				setWidgetSecret(data.widget_secret)
			}
			const reauth = async () => {
				const openIDToken = await matrix.requestOpenIDToken(
					localStorage.mxHomeserver, localStorage.mxUserID, localStorage.mxAccessToken)
				const integrationData = await matrix.requestIntegrationToken(openIDToken)
				localStorage.stickerSetupAccessToken = integrationData.token
				return await sticker.whoami()
			}
			const whoamiErrored = err => {
				console.error("Setup API whoami returned", err)
				if (err.code === "NET.MAUNIUM_TOKEN_EXPIRED" || err.code === "M_UNKNOWN_TOKEN") {
					return reauth().then(whoamiReceived)
				} else {
					throw err
				}
			}
			sticker.whoami().then(whoamiReceived, whoamiErrored).catch(err => {
				setLoading(false)
				setError(err.message)
			})
		}
	}, [])

	if (loading) {
		return html`<${Spinner} size=80 green />`
	}

	return html`${widgetSecret}`
}

export default App
