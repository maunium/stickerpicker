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

export const integrationPrefix = "../_matrix/integrations/v1"

export const queryToURL = (url, query) => {
	if (!Array.isArray(query)) {
		query = Object.entries(query)
	}
	query = query.map(([key, value]) =>
		[key, typeof value === "string" ? value : JSON.stringify(value)])
	url = `${url}?${new URLSearchParams(query)}`
	return url
}

export const tryFetch = async (url, options, reqInfo) => {
	if (options.query) {
		url = queryToURL(url, options.query)
		delete options.query
	}
	options.headers = {
		Authorization: `Bearer ${localStorage.accessToken}`,
		...options.headers,
	}
	const reqName = `${reqInfo.service} ${reqInfo.requestType}`
	let resp
	try {
		resp = await fetch(url, options)
	} catch (err) {
		console.error(reqName, "request failed:", err)
		throw new Error(`Failed to contact ${reqInfo.service}`)
	}
	if (resp.status === 502) {
		console.error("Unexpected", reqName, "request bad gateway:", await resp.text())
		throw new Error(`Failed to contact ${reqInfo.service}`)
	}
	if (reqInfo.raw) {
		return resp
	} else if (resp.status === 204) {
		return
	}
	let data
	try {
		data = await resp.json()
	} catch (err) {
		console.error(reqName, "request JSON parse failed:", err)
		throw new Error(`Invalid response from ${reqInfo.service}`)
	}
	if (resp.status >= 400) {
		console.error("Unexpected", reqName, "request status:", resp.status, data)
		throw new Error(data.error || data.message || `Invalid response from ${reqInfo.service}`)
	}
	return data
}
