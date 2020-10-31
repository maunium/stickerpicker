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
import { useEffect, useLayoutEffect, useRef, useState } from "../../lib/preact/hooks.js"
import { html } from "../../lib/htm/preact.js"

import * as matrix from "./matrix-api.js"
import Button from "../Button.js"
import Spinner from "../Spinner.js"

const query = Object.fromEntries(location.search
	.substr(1).split("&")
	.map(part => part.split("="))
	.map(([key, value = ""]) => [key, value]))

const LoginView = ({ onLoggedIn }) => {
	const usernameWrapperRef = useRef()
	const usernameRef = useRef()
	const serverRef = useRef()
	const passwordRef = useRef()
	const previousServerValue = useRef()
	const [loading, setLoading] = useState(false)
	const [userIDFocused, setUserIDFocused] = useState(false)
	const [supportedFlows, setSupportedFlows] = useState(["m.login.password"])
	const [username, setUsername] = useState("")
	const [server, setServer] = useState("")
	const [serverURL, setServerURL] = useState("")
	const [password, setPassword] = useState("")
	const [error, setError] = useState(null)

	const keyDown = evt => {
		if ((evt.target.name === "username" && evt.key === ":") || evt.key === "Enter") {
			if (evt.target.name === "username") {
				serverRef.current.focus()
			} else if (evt.target.name === "server") {
				passwordRef.current.focus()
			}
			evt.preventDefault()
		} else if (evt.target.name === "server" && !evt.target.value && evt.key === "Backspace") {
			usernameRef.current.focus()
		}
	}

	const paste = evt => {
		if (usernameRef.current.value !== "" || serverRef.current.value !== "") {
			return
		}

		let data = evt.clipboardData.getData("text")
		if (data.startsWith("@")) {
			data = data.substr(1)
		}
		const separator = data.indexOf(":")
		if (separator === -1) {
			setUsername(data)
		} else {
			setUsername(data.substr(0, separator))
			setServer(data.substr(separator + 1))
			serverRef.current.focus()
		}
		evt.preventDefault()
	}

	useLayoutEffect(() => usernameRef.current.focus(), [])
	const onFocus = () => setUserIDFocused(true)
	const onBlur = () => {
		setUserIDFocused(false)
		if (previousServerValue.current !== server && server) {
			previousServerValue.current = server
			setSupportedFlows(null)
			setError(null)
			matrix.resolveWellKnown(server).then(url => {
				setServerURL(url)
				localStorage.mxServerName = server
				localStorage.mxHomeserver = url
				return matrix.getLoginFlows(url)
			}).then(flows => {
				setSupportedFlows(flows)
			}).catch(err => {
				setError(err.message)
				setSupportedFlows(["m.login.password"])
			})
		}
	}

	useEffect(() => {
		if (localStorage.mxHomeserver && query.loginToken) {
			console.log("Found homeserver in localstorage and loginToken in query, " +
				"attempting SSO token login")
			setError(null)
			setLoading(true)
			submit(query.loginToken, localStorage.mxHomeserver)
				.catch(err => console.error("Fatal error:", err))
				.finally(() => setLoading(false))
			const url = new URL(location.href)
			url.searchParams.delete("loginToken")
			history.replaceState({}, document.title, url.toString())
		}
	}, [])

	const submit = async (token, serverURLOverride) => {
		let authInfo
		if (token) {
			authInfo = {
				type: "m.login.token",
				token,
			}
		} else {
			authInfo = {
				type: "m.login.password",
				identifier: {
					type: "m.id.user",
					user: username,
				},
				password,
			}
		}
		try {
			const actualServerURL = serverURLOverride || serverURL
			const [accessToken, userID, realURL] = await matrix.login(actualServerURL, authInfo)
			const openIDToken = await matrix.requestOpenIDToken(realURL, userID, accessToken)
			const integrationData = await matrix.requestIntegrationToken(openIDToken)
			localStorage.mxHomeserver = realURL
			localStorage.mxAccessToken = accessToken
			localStorage.mxUserID = userID
			localStorage.stickerSetupAccessToken = integrationData.token
			onLoggedIn()
		} catch (err) {
			setError(err.message)
		}
	}

	const onSubmit = evt => {
		evt.preventDefault()
		setError(null)
		setLoading(true)
		submit()
			.catch(err => console.error("Fatal error:", err))
			.finally(() => setLoading(false))
	}

	const startSSOLogin = () => {
		const redir = encodeURIComponent(location.href)
		location.href = `${serverURL}/_matrix/client/r0/login/sso/redirect?redirectUrl=${redir}`
	}

	const usernameWrapperClick = evt => evt.target === usernameWrapperRef.current
		&& usernameRef.current.focus()

	const ssoButton = html`
		<${Button} type="button" disabled=${!serverURL} onClick=${startSSOLogin}
				   title=${!serverURL ? "Enter your server name before using SSO" : undefined}>
			${loading ? html`<${Spinner} size=30/>` : "Log in with SSO"}
		</Button>
	`

	const disablePwLogin = !username || !server || !serverURL
	const loginButton = html`
		<${Button} type="submit" disabled=${disablePwLogin}
				   title=${disablePwLogin ? "Fill out the form before submitting" : undefined}>
			${loading ? html`<${Spinner} size=30/>` : "Log in"}
		</Button>
	`

	return html`
		<main class="login-view">
			<form class="login-box ${error ? "has-error" : ""}" onSubmit=${onSubmit}>
				<h1>Stickerpicker setup</h1>
				<div class="username input ${userIDFocused ? "focus" : ""}"
					 ref=${usernameWrapperRef} onClick=${usernameWrapperClick}>
					<span onClick=${() => usernameRef.current.focus()}>@</span>
					<input type="text" placeholder="username" name="username" value=${username}
						   onChange=${evt => setUsername(evt.target.value)} ref=${usernameRef}
						   onKeyDown=${keyDown} onFocus=${onFocus} onBlur=${onBlur}
						   onPaste=${paste}/>
					<span onClick=${() => serverRef.current.focus()}>:</span>
					<input type="text" placeholder="example.com" name="server" value=${server}
						   onChange=${evt => setServer(evt.target.value)} ref=${serverRef}
						   onKeyDown=${keyDown} onFocus=${onFocus} onBlur=${onBlur}/>
				</div>
				<input type="password" placeholder="password" name="password" value=${password}
					   class="password input" ref=${passwordRef}
					   disabled=${supportedFlows && !supportedFlows.includes("m.login.password")}
					   onChange=${evt => setPassword(evt.target.value)}/>
				<div class="button-group">
					${supportedFlows === null && html`<${Spinner} green size=30 />`}
					${supportedFlows?.includes("m.login.sso") && ssoButton}
					${supportedFlows?.includes("m.login.password") && loginButton}
				</div>
				${error && html`<div class="error">${error}</div>`}
			</form>
		</main>`
}

export default LoginView
